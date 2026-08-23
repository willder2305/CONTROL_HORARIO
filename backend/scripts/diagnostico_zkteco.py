import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.fingerprint.real_provider import FingerprintDeviceError, FingerprintDuplicateError, RealFingerprintProvider


def main():
    parser = argparse.ArgumentParser(description="Diagnostico local para lector ZKTeco ZK9500.")
    parser.add_argument(
        "--capturar",
        action="store_true",
        help="Realiza el registro de prueba con tres capturas y reporta el tamano del template.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Segundos de espera para captura cuando se usa --capturar.",
    )
    args = parser.parse_args()

    provider = RealFingerprintProvider(capture_timeout_seconds=args.timeout)
    try:
        status = provider.status()
        for key, value in status.items():
            print(f"{key}={value}")

        if args.capturar:
            template = provider.enroll(active_fingerprints=[])
            print("captura_ok=true")
            print(f"template_bytes={len(template)}")
    except FingerprintDeviceError as error:
        print("ready=false")
        print(f"error={error}")
        return 1
    except FingerprintDuplicateError as error:
        print("ready=false")
        print(f"error={error}")
        return 2

    return 0 if status.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
