# Task 3.2: S3 Presigned URL Generation Fix & Validation

## Overview

Fix the critical S3 presigned URL generation issue that prevents users from downloading invoices. Currently, presigned URLs are generated successfully but return 403 Forbidden errors when accessed, blocking the core download functionality. The issue is not with AWS permissions but with incorrect presigned URL generation patterns.

## Business Context

The invoice download system is a core feature that allows users to:
- Re-download original PDF invoices after processing
- Access invoices for record-keeping and auditing
- Verify processing results against original documents
- Share invoices with accounting or compliance teams

Without working downloads, the system provides upload and processing but no way to retrieve the original documents, significantly reducing its value.

## Problem Analysis

### Current Issue
- **Symptom**: Presigned URLs return 403 Forbidden errors
- **Test Case**: Existing Lawn Fawn invoice fails download despite successful URL generation
- **Impact**: Complete breakdown of download functionality
- **User Experience**: Users cannot access their uploaded invoices

### Root Cause Analysis
Based on analysis of working AWS Console URLs vs our generated URLs:

1. **S3 File Exists**: ✅ Invoice confirmed in S3 (98,631 bytes)
2. **URL Generation**: ✅ Presigned URLs generate successfully
3. **URL Access**: ❌ 403 Forbidden error on access
4. **URL Format**: ❌ Generated URLs missing required parameters
5. **URL Expiration**: ✅ Security works correctly

**Evidence**: AWS Console generates working URLs with different parameter structure and additional required fields.

### Technical Root Cause
The issue is **incorrect presigned URL generation pattern**, not AWS IAM permissions. Our current implementation is missing:

1. **Proper boto3 Pattern**: Not using the recommended AWS SDK pattern
2. **Required Parameters**: Missing AWS signature v4 parameters
3. **Session Token Handling**: Not properly handling temporary credentials
4. **Region Compatibility**: Missing eu-north-1 specific requirements

## Success Criteria

- [ ] Presigned URLs return 200 OK instead of 403 Forbidden
- [ ] Generated URLs match format and structure of working AWS Console URLs
- [ ] Test invoice downloads successfully via generated URLs
- [ ] All S3 operations work correctly (upload, download, delete, metadata)
- [ ] Security measures remain intact (private bucket, URL expiration)
- [ ] URL generation follows AWS best practices and documentation
- [ ] Comprehensive test suite validates presigned URL generation
- [ ] Documentation covers correct S3 presigned URL patterns

## Technical Implementation

### 1. Correct Presigned URL Generation Pattern

**Current (Broken) Implementation:**
```python
# Current S3Manager.generate_download_url() - BROKEN
presigned_url = self.s3_client.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': self.settings.s3_bucket_name,
        'Key': s3_key,
        'ResponseContentDisposition': 'inline'
    },
    ExpiresIn=expires_in
)
```

**Fixed Implementation (AWS Best Practice):**
```python
def generate_presigned_url(s3_client, client_method, method_parameters, expires_in):
    """
    Generate a presigned Amazon S3 URL using correct boto3 pattern.
    
    :param s3_client: A Boto3 Amazon S3 client.
    :param client_method: The name of the client method that the URL performs.
    :param method_parameters: The parameters of the specified client method.
    :param expires_in: The number of seconds the presigned URL is valid for.
    :return: The presigned URL.
    """
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=client_method,
            Params=method_parameters,
            ExpiresIn=expires_in
        )
    except ClientError:
        logger.error(f"Couldn't get a presigned URL for client method '{client_method}'.")
        raise
    return url

# Usage in S3Manager:
def generate_download_url(self, s3_key: str, expires_in: Optional[int] = None) -> Tuple[str, datetime]:
    if expires_in is None:
        expires_in = self.settings.invoice_download_expiration
    
    presigned_url = generate_presigned_url(
        self.s3_client,
        "get_object",
        {
            "Bucket": self.settings.s3_bucket_name,
            "Key": s3_key
        },
        expires_in
    )
    
    expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
    return presigned_url, expiration_time
```

### 2. AWS Console URL Analysis

**Working AWS Console URL Example:**
```
https://sw-product-processing-bucket.s3.eu-north-1.amazonaws.com/invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=...&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Date=...&X-Amz-Expires=3000&X-Amz-SignedHeaders=host&X-Amz-Signature=...
```

**Key Parameters Present in Working URL:**
- `response-content-disposition=inline`
- `X-Amz-Content-Sha256=UNSIGNED-PAYLOAD`
- `X-Amz-Security-Token=...` (temporary credentials)
- `X-Amz-Algorithm=AWS4-HMAC-SHA256`
- `X-Amz-Credential=...`
- `X-Amz-Date=...`
- `X-Amz-Expires=3000`
- `X-Amz-SignedHeaders=host`
- `X-Amz-Signature=...`

### 3. Key Differences to Fix

**Parameter Structure:**
- Use exact boto3 pattern from working examples
- Ensure proper handling of temporary credentials (session tokens)
- Include all required AWS signature v4 parameters
- Match parameter structure of working AWS Console URLs

**S3 Client Configuration:**
```python
# Ensure proper S3 client configuration for eu-north-1
config = boto3.session.Config(
    signature_version='s3v4',  # Required for newer regions
    s3={
        'addressing_style': 'virtual'  # Use virtual-hosted style URLs
    },
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'
    },
    region_name=self.settings.aws_region
)

self.s3_client = session.client('s3', config=config)
```

## Testing Strategy

### 1. Unit Tests
- Test presigned URL generation with correct parameters
- Test URL format validation
- Test expiration time calculation
- Test error handling for invalid keys

### 2. Integration Tests
- Test complete download workflow with real S3 bucket
- Test with existing Lawn Fawn invoice file
- Test with different file sizes and types
- Test concurrent URL generation requests

### 3. Validation Tests
```python
# Test presigned URL generation
def test_presigned_url_generation():
    s3_manager = S3InvoiceManager()
    test_s3_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    # Generate URL
    download_url, expires_at = s3_manager.generate_download_url(test_s3_key)
    
    # Test URL accessibility
    response = requests.head(download_url, timeout=10)
    assert response.status_code == 200
    
    # Test URL format
    assert "X-Amz-Algorithm" in download_url
    assert "X-Amz-Signature" in download_url
    assert "X-Amz-Expires" in download_url

# Test URL expiration
def test_url_expiration():
    s3_manager = S3InvoiceManager()
    test_s3_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    # Generate URL with short expiration
    download_url, expires_at = s3_manager.generate_download_url(test_s3_key, expires_in=5)
    
    # Test immediately
    response = requests.head(download_url, timeout=10)
    assert response.status_code == 200
    
    # Wait for expiration
    time.sleep(6)
    
    # Test after expiration
    response = requests.head(download_url, timeout=10)
    assert response.status_code == 403
```

### 4. Manual Testing Commands
```bash
# Test with existing invoice
cd backend
python test_invoice_download_system.py

# Test AWS CLI access (for comparison)
aws s3 cp s3://sw-product-processing-bucket/invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf ./test-download.pdf

# Generate presigned URL manually for comparison
python -c "
import boto3
s3 = boto3.client('s3', region_name='eu-north-1')
url = s3.generate_presigned_url('get_object', 
    Params={'Bucket': 'sw-product-processing-bucket', 'Key': 'invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf'}, 
    ExpiresIn=3600)
print(url)
"
```

## Implementation Steps

### Phase 1: Fix URL Generation (High Priority)
1. **Update S3Manager.generate_download_url()**
   - Replace current implementation with AWS best practice pattern
   - Use exact boto3 pattern from working examples
   - Remove unnecessary parameters that might cause issues

2. **Test with Existing Invoice**
   ```bash
   python backend/test_invoice_download_system.py
   ```

3. **Validate URL Format**
   - Compare generated URLs with working AWS Console URLs
   - Ensure all required parameters are present
   - Verify signature and authentication parameters

### Phase 2: Comprehensive Testing (Medium Priority)
1. **Create Test Suite**
   - Implement comprehensive presigned URL tests
   - Add automated validation to CI/CD pipeline
   - Test edge cases and error scenarios

2. **Performance Validation**
   - Test URL generation speed and reliability
   - Validate concurrent access patterns
   - Monitor system performance under load

### Phase 3: Documentation (Low Priority)
1. **Technical Documentation**
   - Document correct presigned URL generation patterns
   - Create troubleshooting guide for URL issues
   - Add operational procedures

2. **Monitoring Setup**
   - Configure CloudWatch metrics for URL generation
   - Set up alerts for URL generation failures
   - Create dashboards for download system health

## Error Handling

### 1. URL Generation Errors
```python
try:
    download_url, expires_at = s3_manager.generate_download_url(s3_key)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchKey':
        return {
            "success": False,
            "error": "file_not_found",
            "message": "Invoice file not found in S3",
            "s3_key": s3_key
        }
    elif error_code == 'AccessDenied':
        return {
            "success": False,
            "error": "access_denied",
            "message": "Insufficient permissions to generate download URL",
            "troubleshooting": "Check AWS credentials and S3 permissions"
        }
```

### 2. URL Access Errors
```python
try:
    response = requests.head(download_url, timeout=10)
    if response.status_code != 200:
        return {
            "success": False,
            "error": "url_access_failed",
            "status_code": response.status_code,
            "message": f"Download URL returned {response.status_code}",
            "retry_suggested": True
        }
except requests.exceptions.RequestException as e:
    return {
        "success": False,
        "error": "network_error", 
        "message": f"Failed to access download URL: {e}",
        "retry_suggested": True
    }
```

### 3. Expiration Handling
```python
if datetime.utcnow() > expires_at:
    return {
        "success": False,
        "error": "url_expired",
        "message": "Download URL has expired",
        "action": "Generate new download URL"
    }
```

## Security Considerations

### 1. URL Security
- ✅ Private S3 bucket (no public access)
- ✅ Presigned URLs with expiration (1 hour default)
- ✅ Structured file organization
- ✅ AWS signature v4 authentication
- ✅ Temporary access tokens when using IAM roles

### 2. Access Control
- Minimal required permissions for S3 operations
- Time-limited URL access (configurable expiration)
- No credential exposure in URLs (handled by AWS signatures)
- Audit logging for download activities

### 3. Monitoring
- Track URL generation success/failure rates
- Monitor download access patterns
- Alert on unusual access attempts
- Log all download activities for audit

## Dependencies

- **AWS Account**: Valid AWS credentials with S3 access
- **S3 Bucket**: `sw-product-processing-bucket` in `eu-north-1`
- **Test Files**: Existing invoice files for validation
- **Task 3.1**: Migration System Fix (completed) - Need stable S3 operations

## Deliverables

1. **Updated S3Manager**: Correct presigned URL generation implementation
2. **Test Suite**: Comprehensive presigned URL testing framework
3. **Documentation**: Technical guide for presigned URL patterns
4. **Validation**: Working download system with existing test invoice
5. **Error Handling**: Robust error responses for URL generation issues

## Acceptance Criteria

- [ ] Test invoice downloads successfully with 200 OK response
- [ ] Generated URLs match format and structure of working AWS Console URLs
- [ ] Presigned URLs work for all file types and sizes in the system
- [ ] URL expiration security measures function correctly
- [ ] Comprehensive test suite validates all presigned URL operations
- [ ] Error handling provides clear guidance for URL generation issues
- [ ] Documentation covers correct presigned URL generation patterns
- [ ] System performance meets requirements for concurrent URL generation

## Risk Mitigation

### 1. Technical Risks
- **URL format changes**: Follow AWS best practices and documentation
- **Region compatibility**: Test specifically with eu-north-1 configuration
- **Credential handling**: Ensure proper temporary credential support

### 2. Operational Risks
- **Service disruption**: Test changes thoroughly before deployment
- **Data access loss**: Validate URL generation before removing old code
- **Performance impact**: Monitor URL generation performance

### 3. Security Risks
- **URL exposure**: Ensure URLs contain proper authentication
- **Access control**: Maintain private bucket configuration
- **Audit compliance**: Implement proper logging and monitoring
