# Power BI Setup (Stage 5, optional)

Power BI integration is **off by default** (`ENABLE_POWERBI=false`) because
it requires real Azure infrastructure that this repo can't provision for
you. This guide gets you from zero to a working embed.

## What's real vs. what requires manual work

- **Automated by this codebase:** Azure AD app-only authentication,
  fetching an embed token, embedding an existing report, passing basic
  filters through to that report.
- **Requires you to do it manually, in Power BI Desktop or the Power BI
  service:** designing the report itself — its pages, visuals, and which
  fields/chart types they use. There is no supported Power BI REST API for
  programmatically composing a report's visual layout. Don't expect
  `PowerBIService` to ever do this — see `backend/app/powerbi/service.py`
  for why.

## Steps

1. **Register an Azure AD app** (Azure Portal → App registrations → New
   registration). Note the **Tenant ID** and **Client ID**.
2. Create a **client secret** for the app (Certificates & secrets → New
   client secret). Note the secret value — you can't see it again later.
3. In the **Power BI Admin Portal**, enable "Allow service principals to use
   Power BI APIs" for a security group containing your app registration.
4. **Publish a report** to a Power BI workspace (from Power BI Desktop:
   Publish → choose workspace). Note the **Workspace ID** and **Report ID**
   from the report's URL (`.../groups/<workspace_id>/reports/<report_id>`).
5. **Grant the service principal access** to that workspace (Workspace →
   Access → add the app as a Member or Viewer).
6. Fill in `.env`:
   ```
   ENABLE_POWERBI=true
   POWERBI_TENANT_ID=...
   POWERBI_CLIENT_ID=...
   POWERBI_CLIENT_SECRET=...
   POWERBI_WORKSPACE_ID=...
   POWERBI_REPORT_ID=...
   ```
7. Call `PowerBIService.get_embed_config()` (wire this into a new
   `/api/powerbi/embed` route if you want it exposed) and pass the returned
   `embed_url` + `access_token` to the `powerbi-client` JS SDK in the
   frontend.

## Troubleshooting

- `401` on token generation: the service principal usually needs a few
  minutes to propagate after being added to the security group.
- `403` on `GenerateToken`: the service principal needs at least Viewer
  access on the workspace containing the report.
