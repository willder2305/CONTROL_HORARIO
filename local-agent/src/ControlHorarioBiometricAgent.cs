using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

namespace ControlHorarioBiometricAgent
{
    internal class AgentConfig
    {
        public string ListenUrl = "http://127.0.0.1:8765/";
        public string ServerUrl = "http://127.0.0.1:5000";
        public string DeviceId = "ZK9500-LOCAL-01";
        public string DeviceToken = "";
        public string BridgePath = @"..\..\backend\zk9500_bridge\bin\Zk9500Bridge.exe";
        public int CaptureTimeoutSeconds = 30;
        public List<string> AllowedOrigins = new List<string>();
    }

    internal class BridgeResult
    {
        public int ExitCode;
        public string Stdout = "";
        public string Stderr = "";
        public Dictionary<string, string> Data = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    }

    internal static class Program
    {
        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
        private static AgentConfig Config;

        public static void Main(string[] args)
        {
            Log("Agente iniciado");
            Config = LoadConfig();
            Config.BridgePath = ResolvePath(Config.BridgePath);

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

        private static AgentConfig LoadConfig()
        {
            var config = new AgentConfig();
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;
            var configPath = Path.Combine(baseDir, "appsettings.json");
            if (!File.Exists(configPath))
            {
                var parentExample = Path.GetFullPath(Path.Combine(baseDir, "..", "appsettings.example.json"));
                var localExample = Path.Combine(baseDir, "appsettings.example.json");
                if (File.Exists(localExample)) configPath = localExample;
                else if (File.Exists(parentExample)) configPath = parentExample;
                else return config;
            }

            var parsed = Json.DeserializeObject(File.ReadAllText(configPath)) as Dictionary<string, object>;
            if (parsed == null) return config;

            config.ListenUrl = GetString(parsed, "ListenUrl", config.ListenUrl);
            config.ServerUrl = GetString(parsed, "ServerUrl", config.ServerUrl).TrimEnd('/');
            config.DeviceId = GetString(parsed, "DeviceId", config.DeviceId);
            config.DeviceToken = GetString(parsed, "DeviceToken", config.DeviceToken);
            config.BridgePath = GetString(parsed, "BridgePath", config.BridgePath);
            config.CaptureTimeoutSeconds = GetInt(parsed, "CaptureTimeoutSeconds", config.CaptureTimeoutSeconds);
            config.AllowedOrigins = GetStringList(parsed, "AllowedOrigins");
            return config;
        }

        private static string GetString(Dictionary<string, object> data, string key, string fallback)
        {
            object value;
            if (!data.TryGetValue(key, out value) || value == null) return fallback;
            return Convert.ToString(value);
        }

        private static int GetInt(Dictionary<string, object> data, string key, int fallback)
        {
            object value;
            if (!data.TryGetValue(key, out value) || value == null) return fallback;
            int parsed;
            return int.TryParse(Convert.ToString(value), out parsed) ? parsed : fallback;
        }

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

            var text = Convert.ToString(value);
            foreach (var part in text.Split(','))
            {
                var item = part.Trim();
                if (item.Length > 0) result.Add(item);
            }
            return result;
        }

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
                        { "version", "1.0.0" },
                        { "data", new Dictionary<string, object> {
                            { "service", "ControlHorarioBiometricAgent" },
                            { "status", "running" },
                            { "deviceId", Config.DeviceId },
                            { "version", "1.0.0" }
                        }}
                    });
                    return;
                }

                if (context.Request.HttpMethod == "GET" && path == "/device/status")
                {
                    HandleDeviceStatus(context);
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

        private static void HandleEnroll(HttpListenerContext context)
        {
            var templatesPath = WriteTemplatesFile(FetchFingerprints());
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

        private static void HandleIdentifyAndMark(HttpListenerContext context)
        {
            var templates = FetchFingerprints();
            if (templates.Count == 0)
            {
                WriteJson(context, 404, Error("HUELLA_NO_RECONOCIDA", "No hay huellas activas para identificar."));
                return;
            }

            var templatesPath = WriteTemplatesFile(templates);
            try
            {
                var result = RunBridge(new[] {
                    "identify",
                    "--templates", templatesPath,
                    "--timeout", Config.CaptureTimeoutSeconds.ToString()
                }, Config.CaptureTimeoutSeconds + 20);

                if (GetData(result.Data, "code") == "HUELLA_NO_RECONOCIDA")
                {
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

        private static List<Dictionary<string, string>> FetchFingerprints()
        {
            int statusCode;
            var response = ServerRequest("GET", "/api/agent/fingerprints", null, out statusCode);
            if (statusCode < 200 || statusCode >= 300)
            {
                throw new InvalidOperationException("No se pudieron descargar templates biometrico del servidor: " + response);
            }

            var root = Json.DeserializeObject(response) as Dictionary<string, object>;
            var data = root != null && root.ContainsKey("data") ? root["data"] as Dictionary<string, object> : null;
            var list = data != null && data.ContainsKey("fingerprints") ? data["fingerprints"] as ArrayList : null;
            var result = new List<Dictionary<string, string>>();
            if (list == null) return result;

            foreach (var item in list)
            {
                var row = item as Dictionary<string, object>;
                if (row == null) continue;
                result.Add(new Dictionary<string, string>
                {
                    { "id", Convert.ToString(row["id"]) },
                    { "template", Convert.ToString(row["template"]) }
                });
            }
            return result;
        }

        private static string WriteTemplatesFile(List<Dictionary<string, string>> templates)
        {
            var path = Path.GetTempFileName();
            using (var writer = new StreamWriter(path, false, Encoding.ASCII))
            {
                foreach (var template in templates)
                {
                    writer.WriteLine(template["id"] + "|" + template["template"]);
                }
            }
            return path;
        }

        private static void ForwardServerJson(HttpListenerContext context, string method, string path, string body)
        {
            int statusCode;
            var response = ServerRequest(method, path, body, out statusCode);
            context.Response.StatusCode = statusCode;
            WriteRawJson(context, response);
        }

        private static string ServerRequest(string method, string path, string body, out int statusCode)
        {
            var request = (HttpWebRequest)WebRequest.Create(Config.ServerUrl.TrimEnd('/') + path);
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

        private static BridgeResult RunBridge(string[] args, int timeoutSeconds)
        {
            if (!File.Exists(Config.BridgePath))
            {
                throw new FileNotFoundException("No existe Zk9500Bridge.exe", Config.BridgePath);
            }

            var psi = new ProcessStartInfo
            {
                FileName = Config.BridgePath,
                Arguments = BuildArguments(args),
                WorkingDirectory = Path.GetDirectoryName(Config.BridgePath),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using (var process = Process.Start(psi))
            {
                if (!process.WaitForExit(timeoutSeconds * 1000))
                {
                    try { process.Kill(); } catch { }
                    throw new TimeoutException("Tiempo de espera agotado al comunicarse con el lector ZK9500.");
                }

                var result = new BridgeResult
                {
                    ExitCode = process.ExitCode,
                    Stdout = process.StandardOutput.ReadToEnd(),
                    Stderr = process.StandardError.ReadToEnd()
                };
                result.Data = ParseBridgeOutput(result.Stdout);
                return result;
            }
        }

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

        private static string Quote(string value)
        {
            if (value == null) return "\"\"";
            return "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
        }

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
                    data[line.Substring(0, index).Trim()] = line.Substring(index + 1).Trim();
                }
            }
            return data;
        }

        private static bool IsSuccess(Dictionary<string, string> data)
        {
            return String.Equals(GetData(data, "success"), "true", StringComparison.OrdinalIgnoreCase);
        }

        private static bool GetBool(Dictionary<string, string> data, string key)
        {
            return String.Equals(GetData(data, key), "true", StringComparison.OrdinalIgnoreCase);
        }

        private static int GetInt(Dictionary<string, string> data, string key, int fallback)
        {
            int parsed;
            return int.TryParse(GetData(data, key), out parsed) ? parsed : fallback;
        }

        private static string GetData(Dictionary<string, string> data, string key, string fallback = "")
        {
            string value;
            return data.TryGetValue(key, out value) ? value : fallback;
        }

        private static Dictionary<string, object> Error(string code, string message)
        {
            return new Dictionary<string, object>
            {
                { "success", false },
                { "code", code },
                { "message", message }
            };
        }

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

        private static bool IsAllowedOrigin(string origin)
        {
            foreach (var allowed in Config.AllowedOrigins)
            {
                if (String.Equals(allowed, origin, StringComparison.OrdinalIgnoreCase)) return true;
            }
            return false;
        }

        private static void WriteJson(HttpListenerContext context, int statusCode, object payload)
        {
            context.Response.StatusCode = statusCode;
            WriteRawJson(context, Json.Serialize(payload));
        }

        private static void WriteRawJson(HttpListenerContext context, string payload)
        {
            var bytes = Encoding.UTF8.GetBytes(payload ?? "{}");
            context.Response.ContentType = "application/json; charset=utf-8";
            context.Response.ContentLength64 = bytes.Length;
            context.Response.OutputStream.Write(bytes, 0, bytes.Length);
            context.Response.Close();
        }

        private static string ResolvePath(string path)
        {
            if (Path.IsPathRooted(path)) return path;
            return Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, path));
        }

        private static void SafeDelete(string path)
        {
            try { if (File.Exists(path)) File.Delete(path); } catch { }
        }


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
