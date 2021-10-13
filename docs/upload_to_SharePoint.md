[SharePoint App-Only flow][1] is utilized  (supported by [Office365-REST-Python-Client][2]).  

[Setting up an app-only principal with tenant permissions][3] section describes how to configure it, to summarize it 
consist of two steps:

 1. register App principal (think of it as a "service account")
 2. grant a permissions


Here is an instruction on how to configure SharePoint App-Only flow:

 
>  - permissions granted per site collection and requires a site    collection administrator (in the provided 
>instruction the permissions
> are granter per site collection)


Steps: 

1. Go to the `appregnew.aspx` page in your SharePoint Online site. 
For example, `https://ansys.sharepoint.com/sites/BetaDownloader/_layouts/15/appregnew.aspx`.
2. On this page, click the **Generate** buttons next to the **Client ID** and **Client Secret** fields to generate 
their values.
3. Store the client ID and client secret securely as these credentials can be used to read or update all data in your 
SharePoint Online environment. You will also use them to configure the SharePoint Online connection in application.
4. Under **Title**, specify a title. For example, `Python console`. Under **App Domain**, specify `localhost`. 
Under **Redirect URI**, specify `https://localhost`.

5. Click **Create**.

6. Go to the `appinv.aspx` page on the site collection to grant _site-scoped_ permissions.
`https://ansys.sharepoint.com/sites/BetaDownloader/_layouts/15/appinv.aspx`

7. Specify your **client ID** in the **App Id** field and click Lookup to find your app.
To grant permissions to the app, copy the XML below to the App’s permission request XML field:

```
<AppPermissionRequests AllowAppOnlyPolicy="true">
<AppPermissionRequest Scope="http://sharepoint/content/sitecollection" Right="FullControl" />
</AppPermissionRequests>
```


8. Click **Create**.
9. On the confirmation dialog, click **Trust** It to grant the permissions.




  [1]: https://docs.microsoft.com/en-us/sharepoint/dev/solution-guidance/security-apponly-azureacs
  [2]: https://github.com/vgrem/Office365-REST-Python-Client
  [3]: https://docs.microsoft.com/en-us/sharepoint/dev/solution-guidance/security-apponly-azureacs#setting-up-an-app-only-principal-with-tenant-permissions