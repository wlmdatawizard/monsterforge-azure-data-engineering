from azure.identity import DefaultAzureCredential


def main():
    print("Attempting Azure authentication...")

    credential = DefaultAzureCredential()
    token = credential.get_token("https://storage.azure.com/.default")

    print("✅ Azure authentication successful!")
    print(f"Token preview: {token.token[:30]}...")


if __name__ == "__main__":
    main()
