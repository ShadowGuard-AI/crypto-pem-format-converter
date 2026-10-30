import argparse
import logging
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
    BestAvailableEncryption,
    load_pem_private_key,
    load_pem_public_key
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_parameters
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm, InvalidTag


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Convert between different PEM encoding formats.")

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("-i", "--input-file", help="Path to the input PEM file.")
    input_group.add_argument("-p", "--private-key", help="Paste the private key in PEM format.")
    input_group.add_argument("-u", "--public-key", help="Paste the public key in PEM format.")
    input_group.add_argument("-params", "--dhparams", help="Paste the diffie-hellman parameters in PEM format.")

    # Output options
    parser.add_argument("-o", "--output-file", help="Path to the output PEM file (default: stdout).", default=None)
    parser.add_argument("-f", "--output-format",
                        choices=["PKCS1", "PKCS8", "SubjectPublicKeyInfo", "TraditionalOpenSSL"],
                        default=None,
                        help="Output format (default: PKCS8 for a private key, SubjectPublicKeyInfo for a public key).")

    # Key type option
    parser.add_argument("-t", "--key-type", choices=["private", "public", "dhparams"], default="private",
                        help="Type of key to convert (private, public, dhparams - default: private)")

    # Encryption options
    parser.add_argument("-e", "--encryption", choices=["none", "best"], default="none",
                        help="Encryption to use for private key (none, best - default: none)")
    parser.add_argument("-pw", "--password", help="Password for encrypting private key (required if encryption is 'best').")

    return parser

def convert_pem(input_data, output_file, output_format, key_type, encryption, password):
    """
    Converts the input PEM data to the specified output format.

    Args:
        input_data (str): The PEM-encoded data to convert.
        output_file (str): The path to the output file (or None for stdout).
        output_format (str): The desired output format (PKCS1, PKCS8).
        key_type (str):  The type of key being converted (private, public).
        encryption (str): Encryption method (none, best).
        password (str): Password for encryption (if applicable).
    """
    try:
        if key_type == "private":
            # One password argument does two jobs in this tool: it
            # decrypts the input when the input is encrypted, and it is
            # the password the output is encrypted with when
            # encryption is 'best'. With encryption 'none' an encrypted
            # input plus its password converts to a plain output, which
            # is the combination the examples rely on.
            # Only an encrypted input may be given the password: passing
            # one for a plain key makes the loader reject the key, which
            # made "-e best -pw ..." fail on every unencrypted input,
            # exactly the case that flag combination is for.
            load_password = password if ("ENCRYPTED" in input_data) else None
            private_key = load_pem_private_key(input_data.encode('utf-8'), load_password.encode('utf-8') if load_password else None, backend=default_backend())
            if output_format is None:
                output_format = "PKCS8"
            if output_format == "PKCS1":
                # There is no PrivateFormat.PKCS1 in the cryptography
                # library; naming it raised AttributeError on every
                # PKCS1 run. For an RSA key the traditional OpenSSL form
                # is the PKCS1 form (BEGIN RSA PRIVATE KEY). Other key
                # types have no PKCS1 form at all, so name that instead
                # of failing with a library error.
                from cryptography.hazmat.primitives.asymmetric import rsa as _rsa
                if not isinstance(private_key, _rsa.RSAPrivateKey):
                    raise ValueError("PKCS1 output is only defined for RSA private keys. Use PKCS8 for this key.")
                output_format_enum = PrivateFormat.TraditionalOpenSSL
            elif output_format == "PKCS8":
                output_format_enum = PrivateFormat.PKCS8
            elif output_format == "TraditionalOpenSSL":
                output_format_enum = PrivateFormat.TraditionalOpenSSL
            else:
                raise ValueError("Invalid output format for private key.")

            if encryption == "none":
                encryption_algorithm = NoEncryption()
            elif encryption == "best":
                if not password:
                    raise ValueError("Password is required for 'best' encryption.")
                encryption_algorithm = BestAvailableEncryption(password.encode('utf-8'))
            else:
                raise ValueError("Invalid encryption option.")

            pem_data = private_key.private_bytes(
                encoding=Encoding.PEM,
                format=output_format_enum,
                encryption_algorithm=encryption_algorithm
            )

        elif key_type == "public":
            public_key = load_pem_public_key(input_data.encode('utf-8'), backend=default_backend())
            if output_format is None:
                # A fixed PKCS8 default made every public key run without
                # -f fail, because PKCS8 is a private key format.
                output_format = "SubjectPublicKeyInfo"
            if output_format == "SubjectPublicKeyInfo":
                output_format_enum = PublicFormat.SubjectPublicKeyInfo
            else:
                raise ValueError("Invalid output format for public key. Only SubjectPublicKeyInfo is supported.")

            pem_data = public_key.public_bytes(
                encoding=Encoding.PEM,
                format=output_format_enum
            )

        elif key_type == "dhparams":
            dhparams = load_pem_parameters(input_data.encode('utf-8'), backend=default_backend())

            pem_data = dhparams.parameter_bytes(
                encoding=Encoding.PEM,
                format=serialization.ParameterFormat.PKCS3
            )

        else:
            raise ValueError("Invalid key type.")

        if output_file:
            with open(output_file, "wb") as f:
                f.write(pem_data)
            logging.info(f"PEM data written to {output_file}")
        else:
            print(pem_data.decode('utf-8'), end="")

    except FileNotFoundError:
        logging.error(f"Error: Input file not found.")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
    except InvalidSignature:
        logging.error("Error: Invalid signature. Possible password issue or corrupted file.")
        sys.exit(1)
    except UnsupportedAlgorithm:
         logging.error("Error: Unsupported Algorithm")
         sys.exit(1)
    except InvalidTag:
        logging.error("Error: Invalid Tag")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


def main():
    """
    Main function to execute the PEM format conversion.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    input_data = None
    if args.input_file:
        try:
            with open(args.input_file, "r") as f:
                input_data = f.read()
        except FileNotFoundError:
            logging.error(f"Error: Input file not found: {args.input_file}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Error reading input file: {e}")
            sys.exit(1)
    elif args.private_key:
        input_data = args.private_key
    elif args.public_key:
        input_data = args.public_key
    elif args.dhparams:
        input_data = args.dhparams
    else:
        parser.print_help()  # Show help if no input source is specified.
        sys.exit(1)

    try:
        convert_pem(input_data, args.output_file, args.output_format, args.key_type, args.encryption, args.password)
    except Exception as e:
        logging.error(f"Conversion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
