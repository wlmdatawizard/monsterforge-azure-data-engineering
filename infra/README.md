# MonsterForge Azure infrastructure

Bicep recreates the project's Azure infrastructure. It does not restore deleted Azure data, activate a subscription, or run the Python pipeline.

## Resources

- `monsterforge-rg` resource group, tagged for the portfolio project.
- StorageV2 account using Standard LRS and the Hot tier, with private `raw`, `clean`, `quarantine`, and `reports` containers. HTTPS and Entra authentication are required; anonymous Blob and shared-key access are disabled. The authenticated Blob endpoint remains publicly reachable.
- Storage Blob Data Contributor for the deploying user, scoped to this storage account.
- SQL logical server and `monsterforge` database using the General Purpose serverless free offer: 2 maximum vCores, 32 GiB maximum data, local backup redundancy, `useFreeLimit: true`, and `freeLimitExhaustionBehavior: AutoPause`. There is no paid fallback if this offer is unavailable.
- One SQL firewall rule for your supplied public IPv4 address. It does not enable the broad Allow Azure services rule.

Storage, database, and administrator names match the original project; SQL uses a new name to avoid the failed East US name/location conflict: storage account `monsterforgewlm`, SQL server `monsterforge-sql-wlm-centralus`, database `monsterforge`, and SQL administrator `monsteradmin`. Storage and SQL server names must still be globally available; deployment does not silently choose alternative names. Repeat deployments to the same group target the same resources. Keep the subscription, group, region, administrator login, and password consistent on repeat runs.

## Prerequisites

Use a current Azure CLI (2.76+ recommended) with Bicep installed, PowerShell, and an enabled subscription. The identity needs subscription deployment/resource creation permissions and permission to create role assignments, for example Owner, or Contributor plus Role Based Access Control Administrator at the necessary scope. Register Microsoft.Storage and Microsoft.Sql in the subscription if they are not already registered.

SQL free-offer availability and regional capacity must be confirmed during Azure validation/deployment. Blob operations and storage remain billable. No VM, Spark cluster, private endpoint, or optional paid SQL security add-on is created by these files. Check subscription-level policies or automatically enabled services separately.

## Preview, then deploy

From the repository root, sign in and list your subscriptions. Run each step separately and confirm sign-in succeeds:

```powershell
az login
az account list --output table
az bicep install
```

Find the public IPv4 address of the network where you will run Python. Supply that address, not a local `192.168.*` address. If your public IP changes later, rerun deployment with the new address.

Preview only; this prompts for a SQL password without displaying it:

```powershell
.\infra\deploy.ps1 -SubscriptionId '<subscription-guid>' -ClientIpAddress '<your-public-ipv4>'
```

Review the proposed changes. To actually create resources, invoke explicitly with `-Deploy`:

```powershell
.\infra\deploy.ps1 -SubscriptionId '<subscription-guid>' -ClientIpAddress '<your-public-ipv4>' -Deploy
```

Use a new strong SQL password (12–128 characters and at least three of uppercase, lowercase, digits, and symbols; do not include the administrator login). Store it locally for the pipeline. The script passes it through a temporary process environment variable into a Bicep secure parameter, restores that variable afterward, and does not print the password or write a credentials file. Do not commit passwords or `.env`.

`main.bicepparam` reads process environment variables populated by the script; it contains no credentials. The script verifies the deployed SQL free-limit properties before reporting success. Azure what-if may show role-assignment or provider errors if permissions/registration are missing; address those before deployment. A failed deployment can leave successfully created resources behind.

## Connect the existing Python project

Deployment outputs include the storage account name, SQL host, database name, and SQL username. Update your existing local `.env` without sharing its contents:

```dotenv
AZURE_STORAGE_ACCOUNT=monsterforgewlm
AZURE_SQL_USER=monsteradmin
AZURE_SQL_PASSWORD=<the password you entered>
```

The current SQL loader hard-codes `monsterforge-sql-wlm-centralus.database.windows.net` and database `monsterforge`; both match this template. Confirm these match the deployment outputs before running Python. This documentation does not modify the loader or your `.env` automatically.

Ensure Azure CLI is using the intended subscription before Python authenticates:

```powershell
az account set --subscription '<subscription-guid>'
python -m src.azure.storage
```

Allow time for the new Blob role assignment to propagate. The database may need time to resume after pausing. The SQL loader appends records, so each successful rerun adds another run's data. Bicep does not create the `monsters_clean` table; the existing pandas SQL loader creates it on first load.

## Verify and capture real screenshots

Capture the clean/quarantine terminal summary, the actual Blob upload output, and SQL validation. In the portal, capture the clean/quarantine Blob paths and a SQL query filtered by the new `run_id`. Check actual SQL validation results: the existing main Python runner can still print success after caught SQL failures.

## Remove the cloud environment when finished

The following command deletes the entire project resource group, including its stored data. Only use it after confirming the group contains solely resources you intend to remove and saving your screenshots and data locally:

```powershell
az group delete --subscription '<subscription-guid>' --name monsterforge-rg
```

## References and validation

- [Azure SQL free offer and limits](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-tier?view=azuresql)
- [SQL database Bicep properties](https://learn.microsoft.com/en-us/azure/templates/microsoft.sql/2025-01-01/servers/databases)
- [Subscription-scope deployment](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-to-subscription)

Local compilation checks syntax and resource types. Live what-if, regional/free-tier eligibility, deployment, permissions, and end-to-end pipeline execution require an active Azure subscription and have not been verified here.

## Separate SQL region

Storage and the resource group stay in East US. The SQL server `monsterforge-sql-wlm-centralus` was created successfully through the portal in Central US after both East US and East US 2 rejected SQL provisioning. SQL defaults to `centralus`. Bicep targets that existing server and adds the free-tier database and client firewall rule. Use the same administrator login and password used during portal creation. Preview before deploying; the server may show updates such as TLS settings and project tags. Keep `-Location eastus` for existing storage.
