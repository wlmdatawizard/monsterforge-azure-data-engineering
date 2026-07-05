from azure.identity import DefaultAzureCredential


def main():
    print("Attempting Azure authentication...")

    credential = DefaultAzureCredential()
    token = credential.get_token("https://storage.azure.com/.default")

    print("✅ Azure authentication successful!")
    print(f"Token preview: {token.token[:30]}...")


def get_credential():
    return DefaultAzureCredential()


if __name__ == "__main__":
    main()
