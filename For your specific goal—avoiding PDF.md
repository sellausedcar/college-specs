For your specific goal—avoiding PDF-by-PDF scraping while preserving access to C11 GPA bands and C12 average HS GPA—the best path is to treat the market in three tiers.

First, use collegedata.fyi as the primary structured source for any workflow centered on recent CDS data. It is the only candidate I found that combines a public archive, a canonical field model, bulk-ish snapshot files, a documented API, and explicit C11/C12 field handling. For analyst-grade work, query cds_manifest to discover which schools/years exist, then read cds_fields for C.1101–C.1130, C.1201, and C.1202. That lets you keep provenance via archive_url, source_format, producer, and data_quality_flag. 

Second, use BigFuture as the official cross-check, not as the canonical research dataset. It is valuable because it is official, broad, and current enough to validate whether a school publicly exposes a GPA distribution at all. But because BigFuture transforms the schema, merges bins, and hides some missingness behind a consumer UI, it is better for sanity checking than for reproducible extraction. 

Third, keep a fallback scraping-and-archive layer for the long tail. You will still need it for schools missing from recent aggregators, for older years, and for sites whose documents are behind Box, Drive, SharePoint, or non-indexed institutional pages. The best fallback pattern is to start from institutional archive pages rather than from generic web search each time, and to collect the raw file first, then parse by format. That is also the lesson embedded in collegedata.fyi’s tiered pipeline. 

If you want to access collegedata.fyi programmatically, these published routes are the most useful starting points:

# Snapshot files
curl 'https://www.collegedata.fyi/snapshots/latest/manifest.json'
curl 'https://www.collegedata.fyi/snapshots/latest/schools.jsonl'
curl 'https://www.collegedata.fyi/snapshots/latest/school_facts.jsonl'

# Friendly API
curl 'https://www.collegedata.fyi/api/schools/search?q=mit'
curl 'https://www.collegedata.fyi/api/schools/mit/sources'

# Raw field layer via PostgREST
# Substitute the public anon key documented on the API page
curl 'https://api.collegedata.fyi/rest/v1/cds_fields?select=school_name,canonical_year,field_id,value_num,archive_url,source_format,producer,data_quality_flag&field_id=in.(C.1201,C.1202,C.1101,C.1102,C.1103,C.1104,C.1105,C.1106,C.1107,C.1108,C.1109,C.1110,C.1111,C.1112,C.1113,C.1114,C.1115,C.1116,C.1117,C.1118,C.1119,C.1120,C.1121,C.1122,C.1123,C.1124,C.1125,C.1126,C.1127,C.1128,C.1129,C.1130)'
