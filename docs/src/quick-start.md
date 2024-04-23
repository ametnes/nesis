# Nesis Documentation

Nesis leverages the power of Generative AI to help enterprises search and discover information held in multiple repositories including; 

1. MinIO Object Store
2. Windows Shares for your On-premise repositories.
3. And many more

Through the meticulous compilation and examination of your enterprise's data, Nesis harnesses the capabilities of Generative AI to create 
conversational engagement with the enterprise user. This allows the enterprise user to search through tons of documents in different formats 
and create summaries, comparison as well as suggestions with context that would not have otherwise been obvious.

Any user interaction with Nesis via its chat interface is performed through predictions. For a user to chat with any documents and data, they must 
have permission to create predictions. Permissions are assigned to a user via user roles. See Administration section for details.

## Usage
To chat with documents, you need to first add a document datasource. Supported document datasource include Windows NT Shares, MinIO, S3 buckets. 

### Setup
To chat with your documents using the Document Q&A

1. Add a datasource to your document repository.
2. Create a role and assign a policy with permissions to read from that datasource.
3. Assign the role to the specific user(s).

## Administration
Nesis offers flexible configuration including adding multiple users to access the solution as well as managing their roles and permissions.

### Adding Users
To add a user,

1. Login using your Administrator email and password.
2. On left menu, navigate to **_Settings_** → **_Users_**.
3. Click New User and enter the **Name**, **Email** and **Password** of the user and hit **Create**.

You’ll then need to distribute the email and password to the user

### Managing Roles
Nesis allows the administrator to control who can perform certain actions within Nesis. To best understand the permission structure, we will make some definitions.

1. At the top level of the permission structure, we have the top level objects. These include;

    1. Datasources
    2. Predictions
    3. Roles
    4. Users

2. For each of these options, there is a permitted action. The scope of the actions include;

    1. Read
    2. Create
    3. Delete
    4. Update

A role is defined by a policy defined in JSON and attached to the role. For example

```json title="policy.json" linenums="1"
{
  "items": [
    {
      "action": "create",
      "resource": "predictions/*"
    },
    {
      "action": "read",
      "resource": "datasources/*"
    }
  ]
}
```

The above policy allows the role to

1. Read from all datasources.
2. Create a prediction (all chats are predictions).

For more precise control over who can access a given datasource, Nesis allows you to specify which datasources a given policy is allowed to access. Here is an example policy,


```json title="policy.json" linenums="1"
{
  "items": [
    {
      "action": "create",
      "resource": "predictions/*"
    },
    {
      "action": "read",
      "resource": "datasources/hr-documents"
    }
  ]
}
```

The role is only allowed to

1. **create** **predictions** (All chats are predictions).
2. **read** the `hr-documents` **datasource**.

#### Creating a Role

To create a role;

1. Navigate to **_Settings_** → **_Roles_**.
2. Click **_Add_**.
3. Enter the role name and the policy JSON.
4. Click **_Create_**.

#### Assigning a Role to a User

To assign the new role to a user

1. Navigate to **_Settings_** → **_Users_**.
2. Find the user and click **_Edit_**.
3. Check the role(s) you want to assign
4. Click **Add**

### Managing Datasources

#### Adding Datasources
You connect to your data and document repositories using datasources. To add a new Datasource;

1. Navigate to **_Settings_** → **_Datasources_**.
2. Click **_Add_**.
3. Select the **Type** and enter the **Name** and _Connection details_
4. Click **Add**
