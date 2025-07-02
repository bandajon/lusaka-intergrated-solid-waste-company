# Company Unification Tool Guide

## Overview

The Company Unification Tool helps identify and merge duplicate company entries in your database to improve billing accuracy. This addresses the common issue where the same company gets registered multiple times with slightly different names (e.g., "LISWMC MATERO" vs "LISWMC MATERO LIMITED").

## Features

### 🔍 Intelligent Duplicate Detection
- **Fuzzy String Matching**: Uses multiple algorithms to detect similar company names
- **Prefix Matching**: Identifies cases where one name is a prefix of another
- **Customizable Similarity Threshold**: Adjustable sensitivity for duplicate detection
- **Pattern-Based Search**: Find companies matching specific patterns (e.g., all "BL" companies)

### 📊 Web-Based Interface
- **Visual Review**: Easy-to-use interface to review potential duplicates
- **Batch Operations**: Select multiple groups for merging at once
- **Custom Merge Names**: Override suggested names with your preferred choice
- **Progress Tracking**: Real-time feedback during merge operations

### 🛡️ Safe Merge Operations
- **Preview Before Merge**: Review all changes before executing
- **Soft Delete**: Duplicate entries are marked as "[MERGED]" rather than deleted
- **Audit Trail**: Track which companies were merged and when
- **Export Reports**: Generate detailed reports of duplicate analysis

## How to Use

### 1. Access the Tool
1. Start the Flask application: `python flask_app/run.py`
2. Open your browser and navigate to `http://localhost:5002`
3. Click on "Company Unification" from the main dashboard

### 2. Review Duplicate Groups
The tool automatically scans your company database and presents potential duplicates grouped by similarity:

- **Main Company**: The primary entry (typically the one found first)
- **Similar Companies**: Other entries that match with their similarity percentage
- **Suggested Merge Name**: The tool's recommendation for the final company name

### 3. Make Merge Decisions
For each group:
1. **Select the group** by checking "Merge this group"
2. **Choose the target company** by selecting the radio button next to your preferred entry
3. **Review/Edit the merge name** in the text field provided
4. The tool will automatically show which companies will be merged

### 4. Execute Merges
1. Review your selections in the summary at the bottom
2. Click "Execute Merges" to apply all changes
3. Wait for the operation to complete
4. The page will refresh to show the updated state

## Understanding Similarity Scores

The tool uses several algorithms to calculate similarity:

- **100%**: Exact matches (case-insensitive)
- **90-99%**: Very similar names with minor differences
- **80-89%**: Similar names with moderate differences
- **70-79%**: Potentially related names
- **Below 70%**: Probably not duplicates (default threshold)

## Examples from Your Data

Based on the image you shared, here are examples of duplicates the tool would detect:

1. **LISWMC MATERO** (Rank 1) might be related to other LISWMC entries
2. **LCC/LISWMC** (Rank 2) vs **LCC Cdf** (Rank 7) - potential variations
3. **Lusaka city Council** (Rank 3) - case variations would be detected

## Best Practices

### ⚠️ Before Using
1. **Backup your database** - Always have a recent backup
2. **Test on a small dataset** first to understand the behavior
3. **Review carefully** - Don't merge companies that are actually different entities

### ✅ During Use
1. **Start with high similarity scores** (90%+) for obvious duplicates
2. **Check company details** like location and type_code to confirm they're the same entity
3. **Use descriptive merge names** that clearly identify the company
4. **Work in batches** rather than trying to merge everything at once

### 📋 After Merging
1. **Verify the results** by checking your analytics dashboard
2. **Update any external references** to the merged company IDs
3. **Monitor billing** to ensure accuracy improvements

## Troubleshooting

### Common Issues

**No duplicates found**: 
- Lower the similarity threshold in the code
- Check if your company names are very different
- Verify the database connection is working

**Too many false positives**:
- Increase the similarity threshold
- Review the specific cases and adjust the algorithm if needed

**Merge operation fails**:
- Check database connectivity
- Ensure you have proper permissions
- Verify the company IDs still exist

### Getting Help

1. Check the application logs for error messages
2. Test with the included test script: `python test_company_unifier.py`
3. Review the duplicate analysis report for insights

## Technical Details

### Database Changes
- Duplicate companies are marked as "[MERGED] Original Name"
- The target company may have its name updated
- No data is permanently deleted

### Files Created
- `duplicate_report_TIMESTAMP.json`: Analysis report
- Database audit logs (if configured)

### Configuration
The similarity threshold can be adjusted in `CompanyUnifier.__init__()`:
```python
CompanyUnifier(similarity_threshold=0.7)  # Default: 70%
```

## Integration with Existing Workflow

The Company Unification Tool integrates seamlessly with your existing analytics workflow:

1. **Data Import** → **Company Unification** → **Analytics Dashboard**
2. Regular unification helps maintain clean data for accurate reporting
3. Export reports can be used for compliance and audit purposes

This tool significantly improves billing accuracy by ensuring each company has a single, consistent entry in your system.