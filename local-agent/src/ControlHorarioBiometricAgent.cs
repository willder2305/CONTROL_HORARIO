using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

namespace ControlHorarioBiometricAgent
{
    /// <summary>
    /// Almacena la configuracion no secreta del listener local, backend, identidad del dispositivo y timeout de captura.
    /// </summary>
    internal class AgentConfig
    {
        public string ListenUrl = "http://127.0.0.1:8765/";
        public string ServerUrl = "http://127.0.0.1:5000";
        public string DeviceId = "ZK9500-LOCAL-01";
        public string DeviceToken = "";
        public string BridgePath = @"bridge\Zk9500Bridge.exe";
        public int CaptureTimeoutSeconds = 30;
        public List<string> AllowedOrigins = new List<string>();
    }

    /// <summary>
    /// Conserva el codigo de salida, las salidas y los pares clave-valor devueltos por Zk9500Bridge.
    /// </summary>
    internal class BridgeResult
    {
        public int ExitCode;
        public string Stdout = "";
        public string Stderr = "";
        public string BridgePath = "";
        public string WorkingDirectory = "";
        public string Arguments = "";
        public string Sha256 = "";
        public Dictionary<string, string> Data = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Conserva el resultado seguro de descargar y validar los templates entregados por el backend.
    /// </summary>
    internal class FingerprintFetchResult
    {
        public List<Dictionary<string, string>> Templates = new List<Dictionary<string, string>>();
        public int ServerCount = -1;
        public int InvalidCount;
        public string RuntimeType = "";
        public string ErrorCode = "";
        public string ErrorMessage = "";
    }

    /// <summary>
    /// Agrupa el proceso que expone el agente local o ejecuta el bridge de integracion con ZKFinger.
    /// </summary>
    internal static class Program
    {
        private const string AgentVersion = "1.0.5";
        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
        private static readonly HashSet<string> BridgeProtocolKeys = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "provider", "success", "code", "message", "sdkLoaded", "sdkInitCode",
            "deviceCount", "connected", "opened", "ready", "error", "id", "score",
            "templatesReceived", "templatesValid", "templatesLoaded", "templatesRejected", "template"
        };
        private static AgentConfig Config;
        private static Mutex InstanceMutex;

        /// <summary>
        /// Inicializa el proceso del agente o bridge, procesa el comando solicitado y garantiza la liberacion de recursos nativos.
        /// </summary>
        public static void Main(string[] args)
        {
            Log("Agente iniciado");
            Config = LoadConfig();
            Config.BridgePath = ResolvePath(Config.BridgePath);

            bool createdNew;
            InstanceMutex = new Mutex(true, @"Local\ControlHorarioBiometricAgent", out createdNew);
            if (!createdNew)
            {
                Log("AGENT_ALREADY_RUNNING");
                return;
            }

            if (!Config.ListenUrl.StartsWith("http://127.0.0.1:", StringComparison.OrdinalIgnoreCase)
                && !Config.ListenUrl.StartsWith("http://localhost:", StringComparison.OrdinalIgnoreCase))
            {
                Log("ListenUrl debe apuntar a 127.0.0.1 o localhost.");
                Environment.Exit(2);
            }

            if (!Config.ListenUrl.EndsWith("/", StringComparison.Ordinal))
            {
                Config.ListenUrl += "/";
            }

            try
            {
                var listener = new HttpListener();
                listener.Prefixes.Add(Config.ListenUrl);
                listener.Start();
                Log("ControlHorarioBiometricAgent escuchando en " + Config.ListenUrl);

                while (true)
                {
                    var context = listener.GetContext();
                    ThreadPool.QueueUserWorkItem(_ => HandleRequest(context));
                }
            }
            catch (Exception ex)
            {
                Log("AGENT_START_FAILED type=" + ex.GetType().Name + " message=" + ex.Message + " listenUrl=" + Config.ListenUrl);
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Carga primero la configuracion protegida de ProgramData y conserva los archivos de ejemplo solo para desarrollo.
        /// </summary>
        private static AgentConfig LoadConfig()
        {
            var config = new AgentConfig();
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;
            var programDataConfig = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
                "ControlHorarioBiometricAgent",
                "appsettings.json"
            );
            var localConfig = Path.Combine(baseDir, "appsettings.json");
            var parentExample = Path.GetFullPath(Path.Combine(baseDir, "..", "appsettings.example.json"));
            var localExample = Path.Combine(baseDir, "appsettings.example.json");
            var configPath = "";

            foreach (var candidate in new[] { programDataConfig, localConfig, localExample, parentExample })
            {
                if (File.Exists(candidate))
                {
                    configPath = candidate;
                    break;
                }
            }
            if (String.IsNullOrWhiteSpace(configPath)) return config;

            var parsed = Json.DeserializeObject(File.ReadAllText(configPath)) as Dictionary<string, object>;
            if (parsed == null) return config;

            config.ListenUrl = GetString(parsed, "ListenUrl", config.ListenUrl);
            config.ServerUrl = GetString(parsed, "ServerUrl", config.ServerUrl).TrimEnd('/');
            config.DeviceId = GetString(parsed, "DeviceId", config.DeviceId);
            config.DeviceToken = GetString(parsed, "DeviceToken", config.DeviceToken);
            config.BridgePath = GetString(parsed, "BridgePath", config.BridgePath);
            config.CaptureTimeoutSeconds = GetInt(parsed, "CaptureTimeoutSeconds", config.CaptureTimeoutSeconds);
            config.AllowedOrigins = GetStringList(parsed, "AllowedOrigins");
            Log("Configuracion cargada desde " + configPath);
            return config;
        }

        /// <summary>
        /// Obtiene una cadena de configuracion conservando un valor predeterminado si falta o es nula.
        /// </summary>
        private static string GetString(Dictionary<string, object> data, string key, string fallback)
        {
            object value;
            if (!data.TryGetValue(key, out value) || value == null) return fallback;
            return Convert.ToString(value);
        }

        /// <summary>
        /// Obtiene un entero de configuracion sin fallar ante valores ausentes o invalidos.
        /// </summary>
        private static int GetInt(Dictionary<string, object> data, string key, int fallback)
        {
            object value;
            if (!data.TryGetValue(key, out value) || value == null) return fallback;
            int parsed;
            return int.TryParse(Convert.ToString(value), out parsed) ? parsed : fallback;
        }

        /// <summary>
        /// Normaliza un valor de configuracion a lista de cadenas para AllowedOrigins.
        /// </summary>
        private static List<string> GetStringList(Dictionary<string, object> data, string key)
        {
            var result = new List<string>();
            object value;
            if (!data.TryGetValue(key, out value) || value == null) return result;

            var list = value as ArrayList;
            if (list != null)
            {
                foreach (var item in list)
                {
                    if (item != null) result.Add(Convert.ToString(item));
                }
                return result;
            }

            var enumerable = value as IEnumerable;
            if (enumerable != null && !(value is string))
            {
                foreach (var item in enumerable)
                {
                    if (item != null) result.Add(Convert.ToString(item));
                }
                return result;
            }

            var text = Convert.ToString(value);
            foreach (var part in text.Split(','))
            {
                var item = part.Trim();
                if (item.Length > 0) result.Add(item);
            }
            return result;
        }

        /// <summary>
        /// Enruta las solicitudes HTTP locales del agente hacia health, estado del dispositivo, enrolamiento o identificacion.
        /// </summary>
        private static void HandleRequest(HttpListenerContext context)
        {
            try
            {
                AddCorsHeaders(context);
                if (context.Request.HttpMethod == "OPTIONS")
                {
                    context.Response.StatusCode = 204;
                    context.Response.Close();
                    return;
                }

                var path = context.Request.Url.AbsolutePath.TrimEnd('/').ToLowerInvariant();
                if (path.Length == 0) path = "/";

                if (context.Request.HttpMethod == "GET" && path == "/health")
                {
                    WriteJson(context, 200, new Dictionary<string, object>
                    {
                        { "success", true },
                        { "service", "running" },
                        { "version", AgentVersion },
                        { "data", new Dictionary<string, object> {
                            { "service", "ControlHorarioBiometricAgent" },
                            { "status", "running" },
                            { "deviceId", Config.DeviceId },
                            { "version", AgentVersion }
                        }}
                    });
                    return;
                }

                if (context.Request.HttpMethod == "GET" && path == "/device/status")
                {
                    HandleDeviceStatus(context);
                    return;
                }

                if (context.Request.HttpMethod == "GET" && path == "/diagnostics")
                {
                    HandleDiagnostics(context);
                    return;
                }

                if (context.Request.HttpMethod == "POST" && path == "/enroll")
                {
                    HandleEnroll(context);
                    return;
                }

                if (context.Request.HttpMethod == "POST" && path == "/identify-and-mark")
                {
                    HandleIdentifyAndMark(context);
                    return;
                }

                WriteJson(context, 404, Error("RUTA_NO_ENCONTRADA", "Ruta no encontrada."));
            }
            catch (Exception ex)
            {
                try
                {
                    WriteJson(context, 500, Error("AGENT_ERROR", ex.Message));
                }
                catch
                {
                    context.Response.Close();
                }
            }
        }

        /// <summary>
        /// Consulta el bridge para publicar el estado real del SDK y del lector ZK9500.
        /// </summary>
        private static void HandleDeviceStatus(HttpListenerContext context)
        {
            var result = RunBridge(new[] { "status" }, 20);
            var ready = GetBool(result.Data, "ready") && result.ExitCode == 0;
            var payload = new Dictionary<string, object>
            {
                { "success", true },
                { "data", new Dictionary<string, object> {
                    { "provider", "local_agent" },
                    { "deviceId", Config.DeviceId },
                    { "sdkLoaded", GetBool(result.Data, "sdkLoaded") },
                    { "deviceCount", GetInt(result.Data, "deviceCount", 0) },
                    { "connected", GetBool(result.Data, "connected") },
                    { "opened", GetBool(result.Data, "opened") },
                    { "ready", ready },
                    { "message", ready ? "Lector ZK9500 disponible." : "Lector ZK9500 no disponible." },
                    { "error", GetData(result.Data, "error") }
                }}
            };
            WriteJson(context, 200, payload);
        }

        /// <summary>
        /// Publica el estado operativo del agente sin exponer tokens, templates ni configuracion sensible.
        /// </summary>
        private static void HandleDiagnostics(HttpListenerContext context)
        {
            var fingerprints = FetchFingerprints();
            var bridge = RunBridge(new[] { "status" }, 20);
            var ready = GetBool(bridge.Data, "ready") && bridge.ExitCode == 0;
            WriteJson(context, 200, new Dictionary<string, object>
            {
                { "success", true },
                { "data", new Dictionary<string, object> {
                    { "agentVersion", AgentVersion },
                    { "serverReachable", String.IsNullOrEmpty(fingerprints.ErrorCode) },
                    { "agentAuthorized", String.IsNullOrEmpty(fingerprints.ErrorCode) },
                    { "fingerprintsReportedByServer", fingerprints.ServerCount },
                    { "fingerprintsParsed", fingerprints.Templates.Count },
                    { "invalidTemplates", fingerprints.InvalidCount },
                    { "bridgeAvailable", File.Exists(Config.BridgePath) },
                    { "bridgePath", bridge.BridgePath },
                    { "bridgeFileExists", File.Exists(Config.BridgePath) },
                    { "bridgeSHA256", bridge.Sha256 },
                    { "bridgeExitCode", bridge.ExitCode },
                    { "bridgeStdoutLength", bridge.Stdout.Length },
                    { "bridgeStderrLength", bridge.Stderr.Length },
                    { "sdkLoaded", GetBool(bridge.Data, "sdkLoaded") },
                    { "deviceCount", GetInt(bridge.Data, "deviceCount", 0) },
                    { "connected", GetBool(bridge.Data, "connected") },
                    { "opened", GetBool(bridge.Data, "opened") },
                    { "deviceReady", ready },
                    { "templateLoadError", fingerprints.ErrorCode }
                }}
            });
        }

        /// <summary>
        /// Captura un template mediante el bridge y devuelve unicamente el resultado necesario para el backend.
        /// </summary>
        private static void HandleEnroll(HttpListenerContext context)
        {
            var fingerprints = FetchFingerprints();
            if (!String.IsNullOrEmpty(fingerprints.ErrorCode))
            {
                WriteJson(context, 503, Error(fingerprints.ErrorCode, fingerprints.ErrorMessage));
                return;
            }

            var templatesPath = WriteTemplatesFile(fingerprints.Templates);
            try
            {
                var result = RunBridge(new[] {
                    "enroll",
                    "--templates", templatesPath,
                    "--timeout", Config.CaptureTimeoutSeconds.ToString()
                }, Config.CaptureTimeoutSeconds + 25);

                if (result.ExitCode != 0 || !IsSuccess(result.Data))
                {
                    WriteJson(context, 503, Error(
                        GetData(result.Data, "code", "LECTOR_NO_DISPONIBLE"),
                        GetData(result.Data, "error", "No se pudo capturar la huella.")));
                    return;
                }

                var template = GetData(result.Data, "template");
                if (String.IsNullOrWhiteSpace(template))
                {
                    WriteJson(context, 503, Error("TEMPLATE_NO_GENERADO", "El lector no devolvio template biometrico."));
                    return;
                }

                WriteJson(context, 200, new Dictionary<string, object>
                {
                    { "success", true },
                    { "message", "Huella capturada correctamente." },
                    { "data", new Dictionary<string, object> { { "template_biometrico", template } } }
                });
            }
            finally
            {
                SafeDelete(templatesPath);
            }
        }

        /// <summary>
        /// Descarga templates autorizados, identifica localmente y reenvia la marcacion validada al backend.
        /// </summary>
        private static void HandleIdentifyAndMark(HttpListenerContext context)
        {
            Log("Inicio identify-and-mark");
            var fingerprints = FetchFingerprints();
            if (!String.IsNullOrEmpty(fingerprints.ErrorCode))
            {
                WriteJson(context, 503, Error(fingerprints.ErrorCode, fingerprints.ErrorMessage));
                return;
            }

            if (fingerprints.Templates.Count == 0)
            {
                var code = fingerprints.ServerCount == 0
                    ? "SIN_HUELLAS_REGISTRADAS"
                    : "TEMPLATES_NO_DISPONIBLES";
                WriteJson(context, 404, Error(
                    code,
                    "No existen huellas activas disponibles para identificacion."));
                return;
            }

            var templatesPath = WriteTemplatesFile(fingerprints.Templates);
            try
            {
                Log("Ejecutando Zk9500Bridge identify templates=" + fingerprints.Templates.Count);
                var result = RunBridge(new[] {
                    "identify",
                    "--templates", templatesPath,
                    "--timeout", Config.CaptureTimeoutSeconds.ToString()
                }, Config.CaptureTimeoutSeconds + 20);

                if (GetData(result.Data, "code") == "HUELLA_NO_RECONOCIDA")
                {
                    Log("DBIdentify sin coincidencia");
                    WriteJson(context, 404, Error("HUELLA_NO_RECONOCIDA", "Huella no reconocida."));
                    return;
                }

                if (result.ExitCode != 0 || !IsSuccess(result.Data))
                {
                    WriteJson(context, 503, Error(
                        GetData(result.Data, "code", "LECTOR_NO_DISPONIBLE"),
                        GetData(result.Data, "error", "No se pudo identificar la huella.")));
                    return;
                }

                var identifiedId = GetData(result.Data, "id");
                if (String.IsNullOrWhiteSpace(identifiedId))
                {
                    WriteJson(context, 404, Error("HUELLA_NO_RECONOCIDA", "Huella no reconocida."));
                    return;
                }

                var body = Json.Serialize(new Dictionary<string, object>
                {
                    { "huella_id", identifiedId },
                    { "device_id", Config.DeviceId }
                });
                ForwardServerJson(context, "POST", "/api/agent/marcaciones", body);
            }
            finally
            {
                SafeDelete(templatesPath);
            }
        }

        /// <summary>
        /// Obtiene por canal autenticado los templates activos requeridos para identificacion local, sin datos personales.
        /// </summary>
        private static FingerprintFetchResult FetchFingerprints()
        {
            var result = new FingerprintFetchResult();
            int statusCode;
            try
            {
                Log("Solicitando templates al backend");
                var response = ServerRequest("GET", "/api/agent/fingerprints", null, out statusCode);
                Log("HTTP status backend: " + statusCode);
                if (statusCode < 200 || statusCode >= 300)
                {
                    result.ErrorCode = "BACKEND_NO_DISPONIBLE";
                    result.ErrorMessage = "No se pudieron descargar las huellas registradas del servidor.";
                    return result;
                }

                var root = Json.DeserializeObject(response) as Dictionary<string, object>;
                if (root == null)
                {
                    result.ErrorCode = "ERROR_CARGA_TEMPLATES";
                    result.ErrorMessage = "El servidor devolvio una respuesta de huellas invalida.";
                    return result;
                }

                object rawData;
                if (!root.TryGetValue("data", out rawData) || rawData == null)
                {
                    result.ErrorCode = "ERROR_CARGA_TEMPLATES";
                    result.ErrorMessage = "El servidor no incluyo datos de huellas.";
                    return result;
                }

                var data = rawData as Dictionary<string, object>;
                if (data == null)
                {
                    result.ErrorCode = "ERROR_CARGA_TEMPLATES";
                    result.ErrorMessage = "El formato de datos de huellas no es valido.";
                    return result;
                }

                result.ServerCount = GetObjectInt(data, "count", -1);
                object rawFingerprints;
                if (!data.TryGetValue("fingerprints", out rawFingerprints) || rawFingerprints == null)
                {
                    result.ErrorCode = "ERROR_CARGA_TEMPLATES";
                    result.ErrorMessage = "El servidor no incluyo las huellas disponibles.";
                    return result;
                }

                result.RuntimeType = rawFingerprints.GetType().FullName;
                Log("Tipo runtime fingerprints: " + result.RuntimeType);
                var fingerprints = rawFingerprints as IEnumerable;
                if (fingerprints == null || rawFingerprints is string)
                {
                    result.ErrorCode = "ERROR_CARGA_TEMPLATES";
                    result.ErrorMessage = "El listado de huellas recibido no tiene un formato valido.";
                    return result;
                }

                foreach (var item in fingerprints)
                {
                    var row = item as Dictionary<string, object>;
                    object rawId;
                    object rawTemplate;
                    int fingerprintId;
                    var template = "";
                    if (row == null
                        || !row.TryGetValue("id", out rawId)
                        || !Int32.TryParse(Convert.ToString(rawId), out fingerprintId)
                        || fingerprintId <= 0
                        || !row.TryGetValue("template", out rawTemplate))
                    {
                        result.InvalidCount++;
                        Log("Template invalido sin identificador valido.");
                        continue;
                    }

                    template = Convert.ToString(rawTemplate);
                    try
                    {
                        var decoded = Convert.FromBase64String(template);
                        if (decoded.Length == 0) throw new FormatException();
                    }
                    catch (FormatException)
                    {
                        result.InvalidCount++;
                        Log("Template invalido para huella ID " + fingerprintId);
                        continue;
                    }

                    result.Templates.Add(new Dictionary<string, string>
                    {
                        { "id", fingerprintId.ToString() },
                        { "template", template }
                    });
                }

                Log("Templates reportados=" + result.ServerCount + " validos=" + result.Templates.Count + " invalidos=" + result.InvalidCount);
                if (result.ServerCount > 0 && result.Templates.Count == 0)
                {
                    result.ErrorCode = "ERROR_CARGA_TEMPLATES";
                    result.ErrorMessage = "No fue posible cargar las huellas registradas.";
                }
            }
            catch (WebException ex)
            {
                result.ErrorCode = "BACKEND_NO_DISPONIBLE";
                result.ErrorMessage = "No se pudo conectar con el servidor.";
                Log("Backend no disponible status=" + ex.Status + " message=" + ex.Message);
            }
            catch (Exception ex)
            {
                result.ErrorCode = "ERROR_CARGA_TEMPLATES";
                result.ErrorMessage = "No fue posible cargar las huellas registradas.";
                Log("Error cargando templates: " + ex.GetType().Name + " " + ex.Message);
            }
            return result;
        }

        /// <summary>
        /// Escribe temporalmente los templates autorizados en el formato que consume el bridge y permite su posterior limpieza.
        /// </summary>
        private static string WriteTemplatesFile(List<Dictionary<string, string>> templates)
        {
            var path = Path.GetTempFileName();
            Log("Escribiendo archivo temporal de templates: " + templates.Count);
            using (var writer = new StreamWriter(path, false, Encoding.ASCII))
            {
                foreach (var template in templates)
                {
                    writer.WriteLine(template["id"] + "|" + template["template"]);
                }
            }
            return path;
        }

        /// <summary>
        /// Reenvia una solicitud del agente al backend y conserva su codigo y cuerpo JSON.
        /// </summary>
        private static void ForwardServerJson(HttpListenerContext context, string method, string path, string body)
        {
            int statusCode;
            var response = ServerRequest(method, path, body, out statusCode);
            context.Response.StatusCode = statusCode;
            WriteRawJson(context, response);
        }

        /// <summary>
        /// Realiza una solicitud autenticada al backend usando identidad de dispositivo y token configurados fuera del codigo.
        /// </summary>
        private static string ServerRequest(string method, string path, string body, out int statusCode)
        {
            var uri = new Uri(Config.ServerUrl.TrimEnd('/') + path);
            if (String.Equals(uri.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
            {
                // TLS 1.2 expressed numerically so the agent remains compilable with .NET Framework 4.
                ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072;
            }

            var request = (HttpWebRequest)WebRequest.Create(uri);
            request.Method = method;
            request.Accept = "application/json";
            request.ContentType = "application/json";
            request.Headers["X-Agent-Token"] = Config.DeviceToken;
            request.Headers["X-Agent-Device"] = Config.DeviceId;
            request.Timeout = 30000;

            if (!String.IsNullOrEmpty(body))
            {
                var bytes = Encoding.UTF8.GetBytes(body);
                request.ContentLength = bytes.Length;
                using (var stream = request.GetRequestStream())
                {
                    stream.Write(bytes, 0, bytes.Length);
                }
            }

            try
            {
                using (var response = (HttpWebResponse)request.GetResponse())
                using (var reader = new StreamReader(response.GetResponseStream()))
                {
                    statusCode = (int)response.StatusCode;
                    return reader.ReadToEnd();
                }
            }
            catch (WebException ex)
            {
                var httpResponse = ex.Response as HttpWebResponse;
                if (httpResponse == null) throw;
                using (var reader = new StreamReader(httpResponse.GetResponseStream()))
                {
                    statusCode = (int)httpResponse.StatusCode;
                    return reader.ReadToEnd();
                }
            }
        }

        /// <summary>
        /// Ejecuta el bridge aislado con un limite de tiempo para evitar bloquear el servicio local por una captura fallida.
        /// </summary>
        private static BridgeResult RunBridge(string[] args, int timeoutSeconds)
        {
            if (!File.Exists(Config.BridgePath))
            {
                throw new FileNotFoundException("No existe Zk9500Bridge.exe", Config.BridgePath);
            }

            var workingDirectory = Path.GetDirectoryName(Config.BridgePath);
            var arguments = BuildArguments(args);
            var psi = new ProcessStartInfo
            {
                FileName = Config.BridgePath,
                Arguments = arguments,
                WorkingDirectory = workingDirectory,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            psi.EnvironmentVariables["PATH"] = workingDirectory + ";" + (Environment.GetEnvironmentVariable("PATH") ?? "");

            var hash = CalculateFileSha256(Config.BridgePath);
            Log("[BIOMETRIC] BridgePath: " + Config.BridgePath);
            Log("[BIOMETRIC] BridgeSHA256: " + hash);
            Log("[BIOMETRIC] WorkingDirectory: " + workingDirectory);
            Log("[BIOMETRIC] Arguments: " + SafeBridgeArguments(args));

            using (var process = Process.Start(psi))
            {
                if (process == null) throw new InvalidOperationException("No fue posible iniciar Zk9500Bridge.exe.");
                string stdout = "";
                string stderr = "";
                var stdoutReader = new Thread(() => stdout = process.StandardOutput.ReadToEnd());
                var stderrReader = new Thread(() => stderr = process.StandardError.ReadToEnd());
                stdoutReader.IsBackground = true;
                stderrReader.IsBackground = true;
                stdoutReader.Start();
                stderrReader.Start();
                if (!process.WaitForExit(timeoutSeconds * 1000))
                {
                    try { process.Kill(); } catch { }
                    process.WaitForExit();
                    stdoutReader.Join();
                    stderrReader.Join();
                    throw new TimeoutException("Tiempo de espera agotado al comunicarse con el lector ZK9500.");
                }
                stdoutReader.Join();
                stderrReader.Join();

                var result = new BridgeResult
                {
                    ExitCode = process.ExitCode,
                    Stdout = stdout,
                    Stderr = stderr,
                    BridgePath = Config.BridgePath,
                    WorkingDirectory = workingDirectory,
                    Arguments = SafeBridgeArguments(args),
                    Sha256 = hash
                };
                result.Data = ParseBridgeOutput(result.Stdout);
                Log("Bridge command=" + args[0] + " exitCode=" + result.ExitCode + " stdoutLength=" + result.Stdout.Length + " stderrLength=" + result.Stderr.Length + " code=" + GetData(result.Data, "code"));
                if (String.Equals(args[0], "status", StringComparison.OrdinalIgnoreCase))
                {
                    Log("----- BRIDGE STATUS STDOUT -----\r\n" + result.Stdout + "\r\n----- END STDOUT -----");
                    if (!String.IsNullOrWhiteSpace(result.Stderr))
                    {
                        Log("----- BRIDGE STATUS STDERR -----\r\n" + result.Stderr + "\r\n----- END STDERR -----");
                    }
                }
                return result;
            }
        }

        /// <summary>
        /// Obtiene el hash del bridge para confirmar que el agente ejecuta la misma copia validada manualmente.
        /// </summary>
        private static string CalculateFileSha256(string path)
        {
            try
            {
                using (var stream = File.OpenRead(path))
                using (var sha256 = SHA256.Create())
                {
                    return BitConverter.ToString(sha256.ComputeHash(stream)).Replace("-", "");
                }
            }
            catch (Exception ex)
            {
                Log("No se pudo calcular SHA256 del bridge: " + ex.GetType().Name);
                return "";
            }
        }

        /// <summary>
        /// Evita que los logs del agente expongan rutas temporales de templates durante enrolamiento o identificacion.
        /// </summary>
        private static string SafeBridgeArguments(string[] args)
        {
            return args != null && args.Length > 0 ? args[0] : "";
        }

        /// <summary>
        /// Compone argumentos seguros y entrecomillados para iniciar el bridge externo.
        /// </summary>
        private static string BuildArguments(string[] args)
        {
            var builder = new StringBuilder();
            foreach (var arg in args)
            {
                if (builder.Length > 0) builder.Append(' ');
                builder.Append(Quote(arg));
            }
            return builder.ToString();
        }

        /// <summary>
        /// Escapa un argumento para conservar su contenido al invocar el proceso bridge.
        /// </summary>
        private static string Quote(string value)
        {
            if (value == null) return "\"\"";
            return "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
        }

        /// <summary>
        /// Convierte la salida clave=valor del bridge a un diccionario para el agente.
        /// </summary>
        private static Dictionary<string, string> ParseBridgeOutput(string output)
        {
            var data = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            using (var reader = new StringReader(output ?? ""))
            {
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    var index = line.IndexOf('=');
                    if (index <= 0) continue;
                    var key = line.Substring(0, index).Trim();
                    if (!BridgeProtocolKeys.Contains(key)) continue;
                    data[key] = line.Substring(index + 1).Trim();
                }
            }
            return data;
        }

        /// <summary>
        /// Interpreta el indicador success devuelto por el bridge.
        /// </summary>
        private static bool IsSuccess(Dictionary<string, string> data)
        {
            return String.Equals(GetData(data, "success"), "true", StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// Interpreta como booleano un valor textual devuelto por el bridge.
        /// </summary>
        private static bool GetBool(Dictionary<string, string> data, string key)
        {
            return String.Equals(GetData(data, key), "true", StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// Obtiene un entero de configuracion sin fallar ante valores ausentes o invalidos.
        /// </summary>
        private static int GetInt(Dictionary<string, string> data, string key, int fallback)
        {
            int parsed;
            return int.TryParse(GetData(data, key), out parsed) ? parsed : fallback;
        }

        /// <summary>
        /// Obtiene un entero de un objeto JSON sin asumir el tipo concreto utilizado por JavaScriptSerializer.
        /// </summary>
        private static int GetObjectInt(Dictionary<string, object> data, string key, int fallback)
        {
            object value;
            int parsed;
            return data.TryGetValue(key, out value) && int.TryParse(Convert.ToString(value), out parsed)
                ? parsed
                : fallback;
        }

        /// <summary>
        /// Obtiene un dato del bridge sin distinguir mayusculas de minusculas.
        /// </summary>
        private static string GetData(Dictionary<string, string> data, string key, string fallback = "")
        {
            string value;
            return data.TryGetValue(key, out value) ? value : fallback;
        }

        /// <summary>
        /// Construye o escribe una respuesta de error uniforme para agente o bridge.
        /// </summary>
        private static Dictionary<string, object> Error(string code, string message)
        {
            return new Dictionary<string, object>
            {
                { "success", false },
                { "code", code },
                { "message", message }
            };
        }

        /// <summary>
        /// Aplica CORS unicamente a los origenes configurados para que el agente no quede expuesto a sitios arbitrarios.
        /// </summary>
        private static void AddCorsHeaders(HttpListenerContext context)
        {
            var origin = context.Request.Headers["Origin"];
            if (!String.IsNullOrWhiteSpace(origin) && IsAllowedOrigin(origin))
            {
                context.Response.Headers["Access-Control-Allow-Origin"] = origin;
                context.Response.Headers["Vary"] = "Origin";
            }
            context.Response.Headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
            context.Response.Headers["Access-Control-Allow-Headers"] = "Content-Type";
            context.Response.Headers["Access-Control-Allow-Private-Network"] = "true";
        }

        /// <summary>
        /// Comprueba que el origen de navegador figure en la lista explicita permitida por el agente.
        /// </summary>
        private static bool IsAllowedOrigin(string origin)
        {
            foreach (var allowed in Config.AllowedOrigins)
            {
                if (String.Equals(allowed, origin, StringComparison.OrdinalIgnoreCase)) return true;
            }
            return false;
        }

        /// <summary>
        /// Serializa y envia una respuesta JSON local con el codigo HTTP solicitado.
        /// </summary>
        private static void WriteJson(HttpListenerContext context, int statusCode, object payload)
        {
            context.Response.StatusCode = statusCode;
            WriteRawJson(context, Json.Serialize(payload));
        }

        /// <summary>
        /// Escribe un cuerpo JSON ya preparado y cierra la respuesta HTTP.
        /// </summary>
        private static void WriteRawJson(HttpListenerContext context, string payload)
        {
            var bytes = Encoding.UTF8.GetBytes(payload ?? "{}");
            context.Response.ContentType = "application/json; charset=utf-8";
            context.Response.ContentLength64 = bytes.Length;
            context.Response.OutputStream.Write(bytes, 0, bytes.Length);
            context.Response.Close();
        }

        /// <summary>
        /// Convierte una ruta relativa del agente en una ruta absoluta basada en su directorio de ejecucion.
        /// </summary>
        private static string ResolvePath(string path)
        {
            if (Path.IsPathRooted(path)) return path;
            return Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, path));
        }

        /// <summary>
        /// Elimina de forma tolerante un archivo temporal que pudo contener templates en memoria de trabajo.
        /// </summary>
        private static void SafeDelete(string path)
        {
            try { if (File.Exists(path)) File.Delete(path); } catch { }
        }


        /// <summary>
        /// Registra eventos operativos del agente sin incluir tokens, credenciales ni templates biometricos.
        /// </summary>
        private static void Log(string message)
        {
            try
            {
                var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "ControlHorarioBiometricAgent", "logs");
                Directory.CreateDirectory(root);
                var path = Path.Combine(root, "agent.log");
                RotateLog(path);
                File.AppendAllText(path, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " " + message + Environment.NewLine, Encoding.UTF8);
            }
            catch
            {
            }
        }

        /// <summary>
        /// Rota el archivo de log cuando alcanza un megabyte para limitar su crecimiento.
        /// </summary>
        private static void RotateLog(string path)
        {
            try
            {
                var file = new FileInfo(path);
                if (!file.Exists || file.Length < 1024 * 1024) return;
                var rotated = path + ".1";
                if (File.Exists(rotated)) File.Delete(rotated);
                File.Move(path, rotated);
            }
            catch
            {
            }
        }
    }
}
