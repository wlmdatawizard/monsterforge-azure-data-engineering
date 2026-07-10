# Unique Public Method Parameters
Total unique parameter names: 66
## analytics_logging
- Used: 1 times
- Types: Optional[ForwardRef('BlobAnalyticsLogging')]
- Example methods:
  - BlobServiceClient.set_service_properties
## blob
- Used: 4 times
- Types: str
- Example methods:
  - BlobServiceClient.get_blob_client
  - ContainerClient.delete_blob
  - ContainerClient.download_blob
  - ContainerClient.get_blob_client
## blob_name
- Used: 1 times
- Types: str
- Example methods:
  - BlobClient.from_connection_string
## blob_type
- Used: 2 times
- Types: Union[str, azure.storage.blob._models.BlobType]
- Example methods:
  - ContainerClient.upload_blob
  - BlobClient.upload_blob
## blob_url
- Used: 1 times
- Types: str
- Example methods:
  - BlobClient.from_blob_url
## blobs
- Used: 3 times
- Types: Union[str, Dict[str, Any], azure.storage.blob._models.BlobProperties]
- Example methods:
  - ContainerClient.delete_blobs
  - ContainerClient.set_premium_page_blob_tier_blobs
  - ContainerClient.set_standard_blob_tier_blobs
## block_id
- Used: 2 times
- Types: str
- Example methods:
  - BlobClient.stage_block
  - BlobClient.stage_block_from_url
## block_list
- Used: 1 times
- Types: List[azure.storage.blob._models.BlobBlock]
- Example methods:
  - BlobClient.commit_block_list
## block_list_type
- Used: 1 times
- Types: str
- Example methods:
  - BlobClient.get_block_list
## conn_str
- Used: 3 times
- Types: str
- Example methods:
  - BlobServiceClient.from_connection_string
  - ContainerClient.from_connection_string
  - BlobClient.from_connection_string
## container
- Used: 3 times
- Types: Union[azure.storage.blob._models.ContainerProperties, str]
- Example methods:
  - BlobServiceClient.delete_container
  - BlobServiceClient.get_blob_client
  - BlobServiceClient.get_container_client
## container_name
- Used: 2 times
- Types: str
- Example methods:
  - ContainerClient.from_connection_string
  - BlobClient.from_connection_string
## container_url
- Used: 1 times
- Types: str
- Example methods:
  - ContainerClient.from_container_url
## content_settings
- Used: 4 times
- Types: Optional[ForwardRef('ContentSettings')]
- Example methods:
  - BlobClient.commit_block_list
  - BlobClient.create_append_blob
  - BlobClient.create_page_blob
  - BlobClient.set_http_headers
## copy_id
- Used: 1 times
- Types: Union[str, Dict[str, Any], azure.storage.blob._models.BlobProperties]
- Example methods:
  - BlobClient.abort_copy
## copy_source_url
- Used: 1 times
- Types: str
- Example methods:
  - BlobClient.append_block_from_url
## cors
- Used: 1 times
- Types: Optional[List[azure.storage.blob._models.CorsRule]]
- Example methods:
  - BlobServiceClient.set_service_properties
## credential
- Used: 5 times
- Types: Union[str, Dict[str, str], ForwardRef('AzureNamedKeyCredential'), ForwardRef('AzureSasCredential'), ForwardRef('TokenCredential'), NoneType]
- Example methods:
  - BlobServiceClient.from_connection_string
  - ContainerClient.from_connection_string
  - ContainerClient.from_container_url
  - BlobClient.from_blob_url
  - BlobClient.from_connection_string
## data
- Used: 4 times
- Types: Union[bytes, Iterable[bytes], IO[bytes]], Union[bytes, str, Iterable[~AnyStr], IO[bytes]], Union[bytes, str, Iterable[~AnyStr], IO[~AnyStr]]
- Example methods:
  - ContainerClient.upload_blob
  - BlobClient.append_block
  - BlobClient.stage_block
  - BlobClient.upload_blob
## delegated_user_tid
- Used: 1 times
- Types: Optional[str]
- Example methods:
  - BlobServiceClient.get_user_delegation_key
## delete_retention_policy
- Used: 1 times
- Types: Optional[ForwardRef('RetentionPolicy')]
- Example methods:
  - BlobServiceClient.set_service_properties
## delete_snapshots
- Used: 2 times
- Types: Optional[str]
- Example methods:
  - ContainerClient.delete_blob
  - BlobClient.delete_blob
## deleted_container_name
- Used: 1 times
- Types: str
- Example methods:
  - BlobServiceClient.undelete_container
## deleted_container_version
- Used: 1 times
- Types: str
- Example methods:
  - BlobServiceClient.undelete_container
## delimiter
- Used: 1 times
- Types: str
- Example methods:
  - ContainerClient.walk_blobs
## encoding
- Used: 2 times
- Types: Optional[str]
- Example methods:
  - ContainerClient.download_blob
  - BlobClient.download_blob
## filter_expression
- Used: 2 times
- Types: str
- Example methods:
  - BlobServiceClient.find_blobs_by_tags
  - ContainerClient.find_blobs_by_tags
## hour_metrics
- Used: 1 times
- Types: Optional[ForwardRef('Metrics')]
- Example methods:
  - BlobServiceClient.set_service_properties
## immutability_policy
- Used: 1 times
- Types: ImmutabilityPolicy
- Example methods:
  - BlobClient.set_immutability_policy
## include
- Used: 2 times
- Types: Union[str, List[str], NoneType]
- Example methods:
  - ContainerClient.list_blobs
  - ContainerClient.walk_blobs
## include_metadata
- Used: 1 times
- Types: bool
- Example methods:
  - BlobServiceClient.list_containers
## incremental_copy
- Used: 1 times
- Types: bool
- Example methods:
  - BlobClient.start_copy_from_url
## key_expiry_time
- Used: 1 times
- Types: datetime
- Example methods:
  - BlobServiceClient.get_user_delegation_key
## key_start_time
- Used: 1 times
- Types: datetime
- Example methods:
  - BlobServiceClient.get_user_delegation_key
## kwargs
- Used: 73 times
- Types: Any
- Example methods:
  - BlobServiceClient.create_container
  - BlobServiceClient.delete_container
  - BlobServiceClient.find_blobs_by_tags
  - BlobServiceClient.from_connection_string
  - BlobServiceClient.get_account_information
  - BlobServiceClient.get_service_properties
  - BlobServiceClient.get_service_stats
  - BlobServiceClient.get_user_delegation_key
  - BlobServiceClient.list_containers
  - BlobServiceClient.set_service_properties
  - ... (63 more)
## lease
- Used: 1 times
- Types: Union[ForwardRef('BlobLeaseClient'), str, NoneType]
- Example methods:
  - BlobServiceClient.delete_container
## lease_duration
- Used: 2 times
- Types: int
- Example methods:
  - ContainerClient.acquire_lease
  - BlobClient.acquire_lease
## lease_id
- Used: 2 times
- Types: Optional[str]
- Example methods:
  - ContainerClient.acquire_lease
  - BlobClient.acquire_lease
## legal_hold
- Used: 1 times
- Types: bool
- Example methods:
  - BlobClient.set_legal_hold
## length
- Used: 12 times
- Types: Optional[int], int
- Example methods:
  - ContainerClient.download_blob
  - ContainerClient.upload_blob
  - BlobClient.append_block
  - BlobClient.clear_page
  - BlobClient.download_blob
  - BlobClient.get_page_range_diff_for_managed_disk
  - BlobClient.get_page_ranges
  - BlobClient.list_page_ranges
  - BlobClient.stage_block
  - BlobClient.upload_blob
  - ... (2 more)
## metadata
- Used: 12 times
- Types: Optional[Dict[str, str]]
- Example methods:
  - BlobServiceClient.create_container
  - ContainerClient.create_container
  - ContainerClient.set_container_metadata
  - ContainerClient.upload_blob
  - BlobClient.commit_block_list
  - BlobClient.create_append_blob
  - BlobClient.create_page_blob
  - BlobClient.create_snapshot
  - BlobClient.set_blob_metadata
  - BlobClient.start_copy_from_url
  - ... (2 more)
## minute_metrics
- Used: 1 times
- Types: Optional[ForwardRef('Metrics')]
- Example methods:
  - BlobServiceClient.set_service_properties
## name
- Used: 2 times
- Types: str
- Example methods:
  - BlobServiceClient.create_container
  - ContainerClient.upload_blob
## name_starts_with
- Used: 3 times
- Types: Optional[str]
- Example methods:
  - BlobServiceClient.list_containers
  - ContainerClient.list_blobs
  - ContainerClient.walk_blobs
## offset
- Used: 8 times
- Types: Optional[int], int
- Example methods:
  - ContainerClient.download_blob
  - BlobClient.clear_page
  - BlobClient.download_blob
  - BlobClient.get_page_range_diff_for_managed_disk
  - BlobClient.get_page_ranges
  - BlobClient.list_page_ranges
  - BlobClient.upload_page
  - BlobClient.upload_pages_from_url
## page
- Used: 1 times
- Types: bytes
- Example methods:
  - BlobClient.upload_page
## premium_page_blob_tier
- Used: 3 times
- Types: PremiumPageBlobTier, Union[str, ForwardRef('PremiumPageBlobTier'), NoneType]
- Example methods:
  - ContainerClient.set_premium_page_blob_tier_blobs
  - BlobClient.create_page_blob
  - BlobClient.set_premium_page_blob_tier
## previous_snapshot
- Used: 1 times
- Types: Union[str, Dict[str, Any], NoneType]
- Example methods:
  - BlobClient.list_page_ranges
## previous_snapshot_diff
- Used: 1 times
- Types: Union[str, Dict[str, Any], NoneType]
- Example methods:
  - BlobClient.get_page_ranges
## previous_snapshot_url
- Used: 1 times
- Types: str
- Example methods:
  - BlobClient.get_page_range_diff_for_managed_disk
## public_access
- Used: 3 times
- Types: Union[ForwardRef('PublicAccess'), str, NoneType]
- Example methods:
  - BlobServiceClient.create_container
  - ContainerClient.create_container
  - ContainerClient.set_container_access_policy
## query_expression
- Used: 1 times
- Types: str
- Example methods:
  - BlobClient.query_blob
## sequence_number
- Used: 1 times
- Types: Optional[str]
- Example methods:
  - BlobClient.set_sequence_number
## sequence_number_action
- Used: 1 times
- Types: Union[str, ForwardRef('SequenceNumberAction')]
- Example methods:
  - BlobClient.set_sequence_number
## signed_identifiers
- Used: 1 times
- Types: Dict[str, ForwardRef('AccessPolicy')]
- Example methods:
  - ContainerClient.set_container_access_policy
## size
- Used: 2 times
- Types: int
- Example methods:
  - BlobClient.create_page_blob
  - BlobClient.resize_blob
## snapshot
- Used: 4 times
- Types: Optional[str], Union[str, Dict[str, Any], NoneType]
- Example methods:
  - BlobServiceClient.get_blob_client
  - ContainerClient.get_blob_client
  - BlobClient.from_blob_url
  - BlobClient.from_connection_string
## source_content_md5
- Used: 1 times
- Types: Union[bytes, bytearray, NoneType]
- Example methods:
  - BlobClient.stage_block_from_url
## source_length
- Used: 2 times
- Types: Optional[int]
- Example methods:
  - BlobClient.append_block_from_url
  - BlobClient.stage_block_from_url
## source_offset
- Used: 3 times
- Types: Optional[int], int
- Example methods:
  - BlobClient.append_block_from_url
  - BlobClient.stage_block_from_url
  - BlobClient.upload_pages_from_url
## source_url
- Used: 4 times
- Types: str
- Example methods:
  - BlobClient.stage_block_from_url
  - BlobClient.start_copy_from_url
  - BlobClient.upload_blob_from_url
  - BlobClient.upload_pages_from_url
## standard_blob_tier
- Used: 2 times
- Types: Union[str, ForwardRef('StandardBlobTier'), NoneType], Union[str, ForwardRef('StandardBlobTier')]
- Example methods:
  - ContainerClient.set_standard_blob_tier_blobs
  - BlobClient.set_standard_blob_tier
## static_website
- Used: 1 times
- Types: Optional[ForwardRef('StaticWebsite')]
- Example methods:
  - BlobServiceClient.set_service_properties
## tags
- Used: 1 times
- Types: Optional[Dict[str, str]]
- Example methods:
  - BlobClient.set_blob_tags
## target_version
- Used: 1 times
- Types: Optional[str]
- Example methods:
  - BlobServiceClient.set_service_properties
## version_id
- Used: 2 times
- Types: Optional[str]
- Example methods:
  - BlobServiceClient.get_blob_client
  - ContainerClient.get_blob_client



| Parameter                 | Example                                                                          |
| ------------------------- | -------------------------------------------------------------------------------- |
| analytics_logging         | `BlobAnalyticsLogging()`                                                         |
| blob                      | `"clean/monsters/latest/monsters_clean.csv"`                                     |
| blob_name                 | `"monsters_clean.csv"`                                                           |
| blob_type                 | `"BlockBlob"`                                                                    |
| blob_url                  | `"https://myaccount.blob.core.windows.net/monsterforge-data/clean/monsters.csv"` |
| blobs                     | `["blob1.csv", "blob2.csv"]`                                                     |
| block_id                  | `"block0001"`                                                                    |
| block_list                | `["block0001", "block0002"]`                                                     |
| block_list_type           | `"committed"`                                                                    |
| conn_str                  | `"DefaultEndpointsProtocol=https;AccountName=myaccount;..."`                     |
| container                 | `"monsterforge-data"`                                                            |
| container_name            | `"monsterforge-data"`                                                            |
| container_url             | `"https://myaccount.blob.core.windows.net/monsterforge-data"`                    |
| content_settings          | `ContentSettings(content_type="text/csv")`                                       |
| copy_id                   | `"7d2f3c8a-1234-5678-abcd-123456789abc"`                                         |
| copy_source_url           | `"https://storage.blob.core.windows.net/source/data.csv"`                        |
| cors                      | `[CorsRule(...)]`                                                                |
| credential                | `"my_storage_key"`                                                               |
| data                      | `"Monster data..."`                                                              |
| delegated_user_tid        | `"00000000-0000-0000-0000-000000000000"`                                         |
| delete_retention_policy   | `RetentionPolicy(enabled=True, days=7)`                                          |
| delete_snapshots          | `"include"`                                                                      |
| deleted_container_name    | `"monsterforge-data"`                                                            |
| deleted_container_version | `"1234567890"`                                                                   |
| delimiter                 | `"/"`                                                                            |
| encoding                  | `"utf-8"`                                                                        |
| filter_expression         | `"department = 'finance'"`                                                       |
| ...                       | ...                                                                              |
