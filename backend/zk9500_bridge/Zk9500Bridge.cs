using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using libzkfpcsharp;

namespace HorariosControl.Zk9500Bridge
{
    /// <summary>
    /// Representa un template autorizado con el identificador que DBIdentify devolvera al agente.
    /// </summary>
    internal class TemplateRecord
    {
        public int Id;
        public byte[] Template;
    }

    /// <summary>
    /// Resume la carga de templates en la base temporal del SDK sin exponer datos biometricos.
    /// </summary>
    internal class TemplateLoadSummary
    {
        public int Received;
        public int Valid;
        public int Added;
        public int Rejected;
    }

    /// <summary>
    /// Agrupa el proceso que expone el agente local o ejecuta el bridge de integracion con ZKFinger.
    /// </summary>
    internal class Program
    {
        private const int TemplateSize = 2048;
        private const int RegisterFingerCount = 3;

        private static IntPtr deviceHandle = IntPtr.Zero;
        private static IntPtr databaseHandle = IntPtr.Zero;
        private static byte[] imageBuffer;

        /// <summary>
        /// Inicializa el proceso del agente o bridge, procesa el comando solicitado y garantiza la liberacion de recursos nativos.
        /// </summary>
        [STAThread]
        private static int Main(string[] args)
        {
            try
            {
                string command = args.Length > 0 ? args[0].ToLowerInvariant() : "status";
                int timeoutSeconds = GetIntArg(args, "--timeout", 30);
                string templatesPath = GetStringArg(args, "--templates", null);

                if (command == "status")
                {
                    return Status();
                }
                if (command == "enroll")
                {
                    return Enroll(templatesPath, timeoutSeconds);
                }
                if (command == "identify")
                {
                    return Identify(templatesPath, timeoutSeconds);
                }

                Error("COMANDO_INVALIDO", "Comando no soportado.");
                return 2;
            }
            catch (TimeoutException error)
            {
                Error("CAPTURE_TIMEOUT", error.Message);
                return 7;
            }
            catch (Exception error)
            {
                Error("ERROR_ZK9500", error.Message);
                return 1;
            }
            finally
            {
                CloseDevice();
                zkfp2.Terminate();
            }
        }

        /// <summary>
        /// Inicializa el SDK temporalmente, detecta el lector y publica sus capacidades sin capturar huellas.
        /// </summary>
        private static int Status()
        {
            Console.WriteLine("provider=zk9500");
            Console.WriteLine("sdkLoaded=true");
            Console.Error.WriteLine("[BIOMETRIC] Provider: zk9500");
            Console.Error.WriteLine("[BIOMETRIC] Inicializando ZKFinger SDK 5.3.0.33");

            int ret = zkfp2.Init();
            if (ret != zkfperrdef.ZKFP_ERR_OK)
            {
                Console.WriteLine("ready=false");
                Console.WriteLine("error=No se pudo inicializar ZKFinger SDK. Codigo: " + ret);
                return 1;
            }
            Console.Error.WriteLine("[BIOMETRIC] SDK inicializado");

            int count = zkfp2.GetDeviceCount();
            Console.Error.WriteLine("[BIOMETRIC] Dispositivos encontrados: " + count);
            Console.WriteLine("deviceCount=" + count);
            Console.WriteLine("connected=" + (count > 0).ToString().ToLowerInvariant());
            if (count <= 0)
            {
                Console.WriteLine("opened=false");
                Console.WriteLine("ready=false");
                return 1;
            }

            OpenDevice(0, false);
            Console.WriteLine("opened=true");
            Console.WriteLine("ready=true");
            return 0;
        }

        /// <summary>
        /// Captura tres muestras, rechaza duplicados y fusiona las muestras con DBMerge para crear un template ZKFinger.
        /// </summary>
        private static int Enroll(string templatesPath, int timeoutSeconds)
        {
            OpenDevice(0, true);
            LoadTemplates(templatesPath);

            byte[][] samples = new byte[RegisterFingerCount][];
            int sampleCount = 0;
            while (sampleCount < RegisterFingerCount)
            {
                byte[] captured = CaptureTemplate(timeoutSeconds);
                int duplicateId;
                int duplicateScore;
                int duplicateRet;
                if (IdentifyLoaded(captured, out duplicateId, out duplicateScore, out duplicateRet))
                {
                    Error("HUELLA_DUPLICADA", "Esta huella ya se encuentra registrada en el sistema.");
                    return 3;
                }

                if (sampleCount > 0 && zkfp2.DBMatch(databaseHandle, captured, samples[sampleCount - 1]) <= 0)
                {
                    Error("HUELLAS_NO_COINCIDEN", "Las huellas capturadas no coinciden. Utilice el mismo dedo e intente nuevamente.");
                    return 4;
                }

                samples[sampleCount] = captured;
                sampleCount++;
                if (sampleCount < RegisterFingerCount)
                {
                    WaitForFingerRelease(10);
                }
            }

            byte[] registeredTemplate = new byte[TemplateSize];
            int registeredTemplateLength = TemplateSize;
            int ret = zkfp2.DBMerge(databaseHandle, samples[0], samples[1], samples[2], registeredTemplate, ref registeredTemplateLength);
            if (ret != zkfperrdef.ZKFP_ERR_OK)
            {
                Error("MERGE_FALLIDO", "No se pudo fusionar el template biometrico. Codigo: " + ret);
                return 5;
            }

            Console.WriteLine("success=true");
            Console.WriteLine("template=" + zkfp2.BlobToBase64(registeredTemplate, registeredTemplateLength));
            return 0;
        }

        /// <summary>
        /// Carga templates activos en la base temporal del SDK y encuentra una coincidencia mediante DBIdentify.
        /// </summary>
        private static int Identify(string templatesPath, int timeoutSeconds)
        {
            OpenDevice(0, true);
            TemplateLoadSummary loaded = LoadTemplates(templatesPath);
            if (loaded.Added == 0)
            {
                Error("TEMPLATES_INCOMPATIBLES", "No se pudo cargar ninguna huella valida en el lector.");
                return 6;
            }

            Console.Error.WriteLine("[BIOMETRIC] Esperando huella...");
            byte[] captured = CaptureTemplate(timeoutSeconds);

            int id;
            int score;
            int ret;
            if (IdentifyLoaded(captured, out id, out score, out ret))
            {
                Console.WriteLine("dbIdentifyRet=" + ret);
                Console.WriteLine("success=true");
                Console.WriteLine("id=" + id);
                Console.WriteLine("score=" + score);
                return 0;
            }

            Console.WriteLine("dbIdentifyRet=" + ret);
            Console.WriteLine("id=" + id);
            Console.WriteLine("score=" + score);
            Error("HUELLA_NO_RECONOCIDA", "Huella no reconocida.");
            return 8;
        }

        /// <summary>
        /// Inicializa ZKFinger, abre el dispositivo indicado y prepara la base biometrica y el buffer de imagen.
        /// </summary>
        private static void OpenDevice(int index, bool initializeSdk)
        {
            Console.Error.WriteLine("[BIOMETRIC] Provider: zk9500");
            if (initializeSdk)
            {
                Console.Error.WriteLine("[BIOMETRIC] Inicializando ZKFinger SDK 5.3.0.33");
                int ret = zkfp2.Init();
                if (ret != zkfperrdef.ZKFP_ERR_OK)
                {
                    throw new InvalidOperationException("No se pudo inicializar ZKFinger SDK. Codigo: " + ret);
                }
                Console.Error.WriteLine("[BIOMETRIC] SDK inicializado");
            }

            Console.Error.WriteLine("[BIOMETRIC] Buscando lector");
            int count = zkfp2.GetDeviceCount();
            Console.Error.WriteLine("[BIOMETRIC] Dispositivos encontrados: " + count);
            if (count <= index)
            {
                throw new InvalidOperationException("No se detecto lector ZKTeco ZK9500 conectado.");
            }

            Console.Error.WriteLine("[BIOMETRIC] Abriendo dispositivo " + index);
            deviceHandle = zkfp2.OpenDevice(index);
            if (deviceHandle == IntPtr.Zero)
            {
                throw new InvalidOperationException("No se pudo abrir el lector ZK9500.");
            }

            databaseHandle = zkfp2.DBInit();
            if (databaseHandle == IntPtr.Zero)
            {
                throw new InvalidOperationException("No se pudo inicializar la base biometrica ZKFinger.");
            }

            int width = GetParameterInt(1);
            int height = GetParameterInt(2);
            imageBuffer = new byte[width * height];
            Console.Error.WriteLine("[BIOMETRIC] ZK9500 listo");
        }

        /// <summary>
        /// Lee un parametro entero del lector, como ancho o alto de imagen, mediante ZKFinger.
        /// </summary>
        private static int GetParameterInt(int parameter)
        {
            byte[] value = new byte[4];
            int size = 4;
            zkfp2.GetParameters(deviceHandle, parameter, value, ref size);
            int result = 0;
            zkfp2.ByteArray2Int(value, ref result);
            return result;
        }

        /// <summary>
        /// Espera una captura valida del lector hasta el timeout configurado.
        /// </summary>
        private static byte[] CaptureTemplate(int timeoutSeconds)
        {
            DateTime deadline = DateTime.UtcNow.AddSeconds(timeoutSeconds);
            while (DateTime.UtcNow < deadline)
            {
                byte[] template = new byte[TemplateSize];
                int templateLength = TemplateSize;
                int ret = zkfp2.AcquireFingerprint(deviceHandle, imageBuffer, template, ref templateLength);
                if (ret == zkfperrdef.ZKFP_ERR_OK)
                {
                    Console.Error.WriteLine("[BIOMETRIC] MESSAGE_CAPTURED_OK");
                    Console.Error.WriteLine("[BIOMETRIC] Template recibido");
                    return template;
                }
                Thread.Sleep(200);
            }
            throw new TimeoutException("Tiempo de espera agotado. No se detecto ninguna huella.");
        }

        /// <summary>
        /// Espera que el usuario retire el dedo entre muestras para evitar capturas duplicadas.
        /// </summary>
        private static void WaitForFingerRelease(int timeoutSeconds)
        {
            DateTime deadline = DateTime.UtcNow.AddSeconds(timeoutSeconds);
            while (DateTime.UtcNow < deadline)
            {
                byte[] template = new byte[TemplateSize];
                int templateLength = TemplateSize;
                int ret = zkfp2.AcquireFingerprint(deviceHandle, imageBuffer, template, ref templateLength);
                if (ret != zkfperrdef.ZKFP_ERR_OK)
                {
                    return;
                }
                Thread.Sleep(200);
            }
            throw new TimeoutException("Retire el dedo del lector antes de continuar con la siguiente captura.");
        }

        /// <summary>
        /// Carga los templates autorizados en la base temporal del SDK para DBIdentify y deteccion de duplicados.
        /// </summary>
        private static TemplateLoadSummary LoadTemplates(string templatesPath)
        {
            TemplateLoadSummary summary = new TemplateLoadSummary();
            foreach (TemplateRecord record in ReadTemplates(templatesPath, summary))
            {
                int ret = zkfp2.DBAdd(databaseHandle, record.Id, record.Template);
                if (ret != zkfperrdef.ZKFP_ERR_OK)
                {
                    summary.Rejected++;
                    Console.Error.WriteLine("[BIOMETRIC] DBAdd fallo id=" + record.Id + " codigo=" + ret);
                    continue;
                }
                summary.Added++;
            }
            Console.WriteLine("templatesReceived=" + summary.Received);
            Console.WriteLine("templatesValid=" + summary.Valid);
            Console.WriteLine("templatesLoaded=" + summary.Added);
            Console.WriteLine("templatesRejected=" + summary.Rejected);
            Console.Error.WriteLine("[BIOMETRIC] Templates recibidos=" + summary.Received + " validos=" + summary.Valid + " cargados=" + summary.Added + " rechazados=" + summary.Rejected);
            return summary;
        }

        /// <summary>
        /// Lee los templates autorizados del archivo temporal y los convierte para DBAdd.
        /// </summary>
        private static List<TemplateRecord> ReadTemplates(string templatesPath, TemplateLoadSummary summary)
        {
            List<TemplateRecord> records = new List<TemplateRecord>();
            if (String.IsNullOrEmpty(templatesPath) || !File.Exists(templatesPath))
            {
                return records;
            }

            foreach (string line in File.ReadAllLines(templatesPath))
            {
                if (String.IsNullOrWhiteSpace(line) || line.IndexOf('|') < 0)
                {
                    summary.Rejected++;
                    continue;
                }
                summary.Received++;
                string[] parts = line.Split(new char[] { '|' }, 2);
                int id;
                if (!Int32.TryParse(parts[0], out id) || id <= 0)
                {
                    summary.Rejected++;
                    Console.Error.WriteLine("[BIOMETRIC] Template con ID invalido");
                    continue;
                }

                try
                {
                    byte[] decoded = Convert.FromBase64String(parts[1]);
                    byte[] template = zkfp2.Base64ToBlob(parts[1]);
                    if (decoded.Length == 0 || template == null || template.Length == 0)
                    {
                        throw new FormatException();
                    }
                    summary.Valid++;
                    records.Add(new TemplateRecord
                    {
                        Id = id,
                        Template = template
                    });
                }
                catch (FormatException)
                {
                    summary.Rejected++;
                    Console.Error.WriteLine("[BIOMETRIC] Template Base64 invalido id=" + id);
                }
            }
            return records;
        }

        /// <summary>
        /// Ejecuta DBIdentify sobre la base temporal y valida que el puntaje indique una coincidencia util.
        /// </summary>
        private static bool IdentifyLoaded(byte[] template, out int id, out int score, out int ret)
        {
            id = 0;
            score = 0;
            ret = zkfp2.DBIdentify(databaseHandle, template, ref id, ref score);
            Console.Error.WriteLine("[BIOMETRIC] DBIdentify ret=" + ret + " id=" + id + " score=" + score);
            return ret == zkfperrdef.ZKFP_ERR_OK && id > 0 && score > 0;
        }

        /// <summary>
        /// Libera la base biometrica y el identificador del lector para no dejar el dispositivo bloqueado.
        /// </summary>
        private static void CloseDevice()
        {
            if (databaseHandle != IntPtr.Zero)
            {
                zkfp2.DBFree(databaseHandle);
                databaseHandle = IntPtr.Zero;
            }
            if (deviceHandle != IntPtr.Zero)
            {
                zkfp2.CloseDevice(deviceHandle);
                deviceHandle = IntPtr.Zero;
            }
        }

        /// <summary>
        /// Extrae el valor de un argumento con nombre de la linea de comandos del bridge.
        /// </summary>
        private static string GetStringArg(string[] args, string name, string fallback)
        {
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == name)
                {
                    return args[i + 1];
                }
            }
            return fallback;
        }

        /// <summary>
        /// Extrae y valida un argumento entero de la linea de comandos del bridge.
        /// </summary>
        private static int GetIntArg(string[] args, string name, int fallback)
        {
            string value = GetStringArg(args, name, null);
            int result;
            return Int32.TryParse(value, out result) ? result : fallback;
        }

        /// <summary>
        /// Construye o escribe una respuesta de error uniforme para agente o bridge.
        /// </summary>
        private static void Error(string code, string message)
        {
            Console.WriteLine("success=false");
            Console.WriteLine("code=" + code);
            Console.WriteLine("message=" + message);
        }
    }
}
