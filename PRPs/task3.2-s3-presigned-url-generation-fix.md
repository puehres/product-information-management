name: "Task 3.2: S3 Presigned URL Generation Fix & Validation"
description: |
  Fix the critical S3 presigned URL generation issue that prevents users from downloading invoices. 
  The issue is incorrect boto3 presigned URL generation patterns, not AWS permissions.

## Purpose
Fix the broken invoice download system by implementing correct AWS S3 presigned URL generation patterns using boto3 best practices.

## Core Principles
1. **Context is King**: Include ALL necessary AWS documentation and working examples
2. **Validation Loops**: Provide executable tests the AI can run to validate URL generation
3. **Information Dense**: Use proven boto3 patterns from AWS documentation
4. **Progressive Success**: Fix URL generation first, then validate with existing test invoice
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Fix the S3 presigned URL generation in `S3InvoiceManager.generate_download_url()` method to return working URLs that allow users to download invoices with 200 OK responses instead of 403 Forbidden errors.

## Why
- **Business Critical**: Users cannot download their uploaded invoices, breaking core functionality
- **User Impact**: Complete breakdown of download workflow affects invoice management
- **System Integrity**: Download capability is essential for audit trails and record-keeping
- **Technical Debt**: Current implementation uses incorrect boto3 patterns

## What
Fix the `generate_download_url()` method in `backend/app/services/s3_manager.py` to use correct AWS boto3 presigned URL generation patterns that produce working download URLs.

### Success Criteria
- [ ] Presigned URLs return 200 OK instead of 403 Forbidden when accessed
- [ ] Test invoice `invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf` downloads successfully
- [ ] Generated URLs match format and structure of working AWS Console URLs
- [ ] All existing S3 operations continue to work (upload, delete, metadata)
- [ ] URL expiration security measures remain intact
- [ ] Comprehensive test suite validates presigned URL generation

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
  why: Official AWS documentation for presigned URL generation patterns
  
- url: https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html
  why: AWS S3 presigned URL best practices and security considerations
  
- file: backend/app/services/s3_manager.py
  why: Current broken implementation that needs fixing
  
- file: backend/test_invoice_download_system.py
  why: Existing test that demonstrates the 403 error and validation workflow
  
- file: backend/tests/connectivity/test_s3_connectivity.py
  why: Testing patterns for S3 operations and validation approach
  
- file: backend/S3_DOWNLOAD_ANALYSIS.md
  why: Detailed analysis of the problem and working AWS Console URL example
  
- file: features/task3.2-s3-presigned-url-generation-fix.md
  why: Complete problem analysis and AWS Console URL structure
```

### Current Codebase tree (relevant S3 components)
```bash
backend/
├── app/
│   ├── services/
│   │   └── s3_manager.py              # BROKEN: generate_download_url() method
│   ├── core/
│   │   └── config.py                  # S3 configuration settings
│   └── models/
│       └── invoice.py                 # S3UploadError exception class
├── tests/
│   └── connectivity/
│       └── test_s3_connectivity.py    # S3 testing patterns
├── test_invoice_download_system.py    # Integration test showing 403 error
└── S3_DOWNLOAD_ANALYSIS.md           # Problem analysis and working URL example
```

### Desired Codebase tree with files to be added and responsibility of file
```bash
backend/
├── app/
│   └── services/
│       └── s3_manager.py              # FIXED: generate_download_url() method
├── tests/
│   ├── connectivity/
│   │   └── test_s3_connectivity.py    # ENHANCED: presigned URL validation tests
│   └── test_s3_presigned_urls.py      # NEW: comprehensive presigned URL tests
└── test_invoice_download_system.py    # VALIDATED: should pass with 200 OK
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: boto3 requires specific parameter structure for presigned URLs
# Current BROKEN pattern:
presigned_url = self.s3_client.generate_presigned_url(
    'get_object',  # ❌ Wrong: should be ClientMethod parameter
    Params={'Bucket': bucket, 'Key': key, 'ResponseContentDisposition': 'inline'},
    ExpiresIn=expires_in
)

# CORRECT pattern from AWS documentation:
presigned_url = self.s3_client.generate_presigned_url(
    ClientMethod='get_object',  # ✅ Correct: explicit ClientMethod
    Params={'Bucket': bucket, 'Key': key},  # ✅ Minimal required params
    ExpiresIn=expires_in
)

# GOTCHA: eu-north-1 region requires signature_version='s3v4' (already configured)
# GOTCHA: ResponseContentDisposition parameter may cause signature issues
# GOTCHA: Temporary credentials (session tokens) are handled automatically by boto3
# GOTCHA: Our S3 client is already properly configured with virtual addressing
```

### Working AWS Console URL Example (for reference)
```
https://sw-product-processing-bucket.s3.eu-north-1.amazonaws.com/invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=...&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Date=...&X-Amz-Expires=3000&X-Amz-SignedHeaders=host&X-Amz-Signature=...
```

## Implementation Blueprint

### Data models and structure
No new data models required. The existing `S3InvoiceManager` class and return types are correct:
```python
# Existing return type is correct:
def generate_download_url(self, s3_key: str, expires_in: Optional[int] = None) -> Tuple[str, datetime]:
    # Returns: (presigned_url, expiration_datetime)
```

### List of tasks to be completed to fulfill the PRP in the order they should be completed

```yaml
Task 1: Fix S3Manager.generate_download_url() method
MODIFY backend/app/services/s3_manager.py:
  - FIND method: "def generate_download_url"
  - REPLACE the presigned URL generation logic
  - PRESERVE existing error handling and logging
  - KEEP existing method signature and return type

Task 2: Create comprehensive presigned URL tests
CREATE backend/tests/test_s3_presigned_urls.py:
  - MIRROR pattern from: backend/tests/connectivity/test_s3_connectivity.py
  - ADD specific presigned URL validation tests
  - INCLUDE URL format validation and accessibility tests

Task 3: Enhance existing connectivity tests
MODIFY backend/tests/connectivity/test_s3_connectivity.py:
  - FIND presigned URL test section
  - ENHANCE with URL accessibility validation
  - ADD URL format structure validation

Task 4: Validate fix with existing test
RUN backend/test_invoice_download_system.py:
  - VERIFY 200 OK response instead of 403 Forbidden
  - CONFIRM test invoice downloads successfully
  - VALIDATE complete workflow functionality
```

### Per task pseudocode

```python
# Task 1: Fix generate_download_url() method
def generate_download_url(self, s3_key: str, expires_in: Optional[int] = None) -> Tuple[str, datetime]:
    """Generate presigned URL using correct boto3 pattern."""
    try:
        if expires_in is None:
            expires_in = self.settings.invoice_download_expiration
        
        logger.info("Generating presigned download URL", s3_key=s3_key, expires_in=expires_in)
        
        # CRITICAL: Use correct boto3 pattern from AWS documentation
        presigned_url = self.s3_client.generate_presigned_url(
            ClientMethod='get_object',  # ✅ Explicit ClientMethod parameter
            Params={
                'Bucket': self.settings.s3_bucket_name,
                'Key': s3_key
                # ✅ Remove ResponseContentDisposition - may cause signature issues
            },
            ExpiresIn=expires_in
        )
        
        expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
        logger.info("Presigned URL generated successfully", s3_key=s3_key)
        
        return presigned_url, expiration_time
        
    except ClientError as e:
        # PRESERVE existing error handling
        error_code = e.response['Error']['Code']
        logger.error("Failed to generate presigned URL", s3_key=s3_key, error_code=error_code)
        raise S3UploadError(f"Failed to generate download URL: {error_code}")

# Task 2: Comprehensive presigned URL tests
def test_presigned_url_generation():
    """Test presigned URL generation and accessibility."""
    s3_manager = S3InvoiceManager()
    test_s3_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    # Generate URL
    download_url, expires_at = s3_manager.generate_download_url(test_s3_key)
    
    # Validate URL format
    assert "X-Amz-Algorithm" in download_url
    assert "X-Amz-Signature" in download_url
    assert "X-Amz-Expires" in download_url
    
    # Test URL accessibility
    response = requests.head(download_url, timeout=10)
    assert response.status_code == 200  # ✅ Should be 200, not 403

def test_url_expiration():
    """Test URL expiration behavior."""
    s3_manager = S3InvoiceManager()
    test_s3_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    # Generate URL with short expiration
    download_url, expires_at = s3_manager.generate_download_url(test_s3_key, expires_in=5)
    
    # Test immediately (should work)
    response = requests.head(download_url, timeout=10)
    assert response.status_code == 200
    
    # Wait for expiration
    time.sleep(6)
    
    # Test after expiration (should fail)
    response = requests.head(download_url, timeout=10)
    assert response.status_code == 403
```

### Integration Points
```yaml
EXISTING_INTEGRATION:
  - S3InvoiceManager: Already integrated with invoice processing system
  - Configuration: S3 settings already in backend/app/core/config.py
  - Error handling: S3UploadError already defined in backend/app/models/invoice.py
  - Logging: structlog already configured and used

NO_NEW_INTEGRATION_REQUIRED:
  - Database: No schema changes needed
  - API routes: Existing routes will work with fixed URLs
  - Frontend: No changes needed - URLs will just work
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd backend
ruff check app/services/s3_manager.py --fix  # Auto-fix what's possible
mypy app/services/s3_manager.py              # Type checking

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE backend/tests/test_s3_presigned_urls.py with these test cases:
def test_presigned_url_format():
    """Generated URLs have correct AWS signature format"""
    s3_manager = S3InvoiceManager()
    url, _ = s3_manager.generate_download_url("test/key.pdf")
    
    # Validate AWS signature components
    assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in url
    assert "X-Amz-Signature=" in url
    assert "X-Amz-Expires=" in url
    assert "X-Amz-Date=" in url

def test_presigned_url_accessibility():
    """Generated URLs return 200 OK when accessed"""
    s3_manager = S3InvoiceManager()
    test_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    url, _ = s3_manager.generate_download_url(test_key)
    response = requests.head(url, timeout=10)
    
    assert response.status_code == 200  # ✅ CRITICAL: Must be 200, not 403

def test_url_expiration_security():
    """URLs properly expire after configured time"""
    s3_manager = S3InvoiceManager()
    test_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    url, _ = s3_manager.generate_download_url(test_key, expires_in=5)
    
    # Should work immediately
    response = requests.head(url, timeout=10)
    assert response.status_code == 200
    
    # Should fail after expiration
    time.sleep(6)
    response = requests.head(url, timeout=10)
    assert response.status_code == 403
```

```bash
# Run and iterate until passing:
cd backend
python -m pytest tests/test_s3_presigned_urls.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test with existing integration test
cd backend
python test_invoice_download_system.py

# Expected output change:
# BEFORE (broken): "❌ Download URL failed: 403"
# AFTER (fixed):   "✅ Download URL is accessible"

# If still failing: Check logs and URL format, ensure boto3 pattern is correct
```

## Testing Strategy (MANDATORY)

### Backend Tests
- [ ] Unit tests for presigned URL generation format
- [ ] Integration tests for URL accessibility with real S3 files
- [ ] URL expiration security validation tests
- [ ] Error handling tests for invalid S3 keys

### Test Execution Plan
- [ ] Run existing S3 connectivity tests to ensure no regression
- [ ] Add new presigned URL specific tests
- [ ] Validate with existing test invoice file
- [ ] Test URL expiration behavior

### Validation Commands
```bash
# 1. Syntax and type checking
cd backend
ruff check app/services/s3_manager.py --fix
mypy app/services/s3_manager.py

# 2. Unit tests
python -m pytest tests/test_s3_presigned_urls.py -v

# 3. Integration test
python test_invoice_download_system.py

# 4. Existing connectivity tests (regression check)
python -m pytest tests/connectivity/test_s3_connectivity.py -v
```

## Documentation Updates Required (MANDATORY)

### Core Documentation
- [ ] Update backend/S3_DOWNLOAD_ANALYSIS.md with fix details
- [ ] Document correct boto3 presigned URL patterns
- [ ] Add troubleshooting guide for future URL issues

### Code Documentation
- [ ] Add docstring to fixed generate_download_url() method
- [ ] Add inline comments explaining boto3 pattern choice
- [ ] Document why ResponseContentDisposition was removed

## Final validation Checklist
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `ruff check app/`
- [ ] No type errors: `mypy app/`
- [ ] Integration test successful: `python test_invoice_download_system.py`
- [ ] Test invoice returns 200 OK instead of 403 Forbidden
- [ ] URL expiration security still works
- [ ] All S3 operations continue to function
- [ ] Documentation updated as specified above
- [ ] Ready for PRP completion workflow

---

## Anti-Patterns to Avoid
- ❌ Don't add unnecessary parameters to presigned URL generation
- ❌ Don't modify S3 client configuration - it's already correct
- ❌ Don't change method signatures or return types
- ❌ Don't remove existing error handling or logging
- ❌ Don't skip testing with the actual test invoice file
- ❌ Don't ignore URL expiration security validation
- ❌ Don't assume the fix works without running integration tests
- ❌ Don't modify unrelated S3 operations (upload, delete, metadata)

## Critical Success Factors
1. **Use exact boto3 pattern from AWS documentation**
2. **Remove ResponseContentDisposition parameter that may cause signature issues**
3. **Validate with real test invoice file, not just unit tests**
4. **Ensure 200 OK response instead of 403 Forbidden**
5. **Maintain all existing security measures and expiration behavior**

## Confidence Score: 9/10
High confidence for one-pass implementation success due to:
- Clear root cause identified (incorrect boto3 pattern)
- Exact fix pattern provided from AWS documentation
- Comprehensive validation with existing test invoice
- Minimal scope (single method fix)
- Extensive context and gotchas documented
