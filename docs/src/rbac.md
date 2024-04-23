# Authentication and Authorization

All users must be _**authenticated**_ before they can use Nesis. As the user interacts with Nesis,
the backend validates authentication for each request.

Each action performed by the user after they have authenticated must be _**authorized**_ by the Nesis.
Permission are issued by an Administrator. It important to note that they term administrator in this case means a user who has permission to issue any given permission.

## Sequences
### Authentication

``` mermaid
sequenceDiagram
  autonumber
  actor User
  User->>Frontend: email, password
  Frontend->>API: email, password
  API->>API: Validate email, password
  alt is valid
    API->>Frontend: Auth token, 200
    Frontend->>User: redirect to landing page
  else not valid
    API->>Frontend: 401
    Frontend->>User: error message
  end
```


### Authorization Sequence
This sequence assumes a role has been created. As a use case, suppose the user is adding a datasource. The authentication
sequence above would need to have been passed.

``` mermaid
sequenceDiagram
  autonumber
  actor User
  User->>Frontend: Auth token, datasource
  Frontend->>API: Auth token, datasource
  API->>API: validate token
  alt token is not valid
    API->>Frontend: 401
    Frontend->>User: error message
  end
  API->>API: check CREATE action on datasource
  alt no action exists
    API->>Frontend: 403
    Frontend->>User: error message
  else action exists:
    API->>API: create datasource
    API->>API: create tasks
    API->>Frontend: 200, created datasource
    Frontend->>User: sucess message
  end
```

## Roles in Nesis

### Overview
A role is a named construct that combines a set of policies and attached to a user. The policy of the role
indicates what actions that bearer (user) of that role is allowed to perform. A tabular description of the actors is below;

| Actor  | Description                                                                                       |
|--------|---------------------------------------------------------------------------------------------------|
| User   | The system user and bearer of the role                                                            |
| Policy | A set of rules that indicate that actions are permitted. By default all actions are not permitted |
| Role   | A named object with a policy attached. A role is then assigned to a user.                         |

!!! note 

    If you are familiar with AWS's roles and policy, you'll notece that Nesis' rbac roles and policies 
    are similar to AWS' roles and policies.

A user can be assigned one or multiple roles.

### Policies
A policy is a set of actions that are attached to the role. The actions are currently CREATE, READ, DELETE and UPDATE.
For a user to perform any of these actions to any object within Nesis, they must have a permitted role attached to them.

The objects in Nesis that require policies to operate include.

| Object     | Description                                                                   |
|------------|-------------------------------------------------------------------------------|
| User       | The system user                                                               |
| Role       | A role created on the system and containing policies.                         |
| Datasource | A datasource that Nesis sources data from.                                    |
| Task       | A scheduled job that runs in the background such as datasource ingestion jobs |
| Prediction | Any user interaction with the rag engine is a prediction.                     |

Some actions require more than policy rule. For example to add a datasource that has a cron schedule,
the user role must permit CREATE:/datasource and CREATE:/tasks.

This fine-grained control enables you to be flexible in your role based access control.

A policy is simply a JSON document that is in the format

```json title="policy.json" linenums="1"
{
  "items": 
    [
      {
        "action": "<action-name>", 
        "resource": "<object>/<object-name>"
      },
      {
        "action": "<action-name>", 
        "resource": "<object>/<object-name>"
      }
    ]
}
```

Where `<object>` can be one of the objects in the table above.

### Attaching to a User
A role must be created first before it can be attached to a user. When a role is created, policy
rules must be assigned to the role.

You can attach a role to a user during creation of the user or after. Role policy enforcement is done
in real time and on every request to the API backend so any changes to the policy will be effective immediately
on the next request to the backend.

#### Examples
Here is a list of examples showing how roles can be applied within Nesis.

##### Example 1

You want to control which user can list and read users in your Nesis instance.

```json title="role.json" linenums="1"
{
  "name": "user-reader",
  "policy": {
    "items": [
      {
        "action": "read", 
        "resource": "users/*"
      }
    ]
  }
}
```

##### Example 2

You want to control which user can administer (create, read, update, delete) users in your Nesis instance. 

```json title="role.json" linenums="1"
{
  "name": "user-reader",
  "policy": {
    "items": [
      {
        "action": "create", 
        "resource": "users/*"
      },
      {
        "action": "read", 
        "resource": "users/*"
      },
      {
        "action": "delete", 
        "resource": "users/*"
      },
      {
        "action": "update", 
        "resource": "users/*"
      }
    ]
  }
}
```

##### Example 3

Requirements for a role that allows the bearer to onlu.

1. Create a datasource.
2. Create a task.
3. Update any task.
4. Update the `general-hr-documents`.


```json title="role.json" linenums="1"
{
  "name": "datasource-task-manager",
  "policy": {
    "items": [
      {
        "action": "create", 
        "resource": "tasks/*"
      },
      {
        "action": "read", 
        "resource": "datasources/*"
      },
      {
        "action": "update", 
        "resource": "datasources/general-hr-documents"
      },
      {
        "action": "update", 
        "resource": "tasks/*"
      }
    ]
  }
}
```

Any attempt by the bearer of this role to perform any other action will be denied.

An alternative way to express this role would be



```json title="role.json" linenums="1" hl_lines="13 14 15 16 17 18 19"
{
  "name": "datasource-task-manager",
  "policy": {
    "items": [
      {
        "action": "create", 
        "resource": "tasks/*"
      },
      {
        "action": "read", 
        "resource": "datasources/*"
      },
      {
        "action": "update", 
        "resources": [
          "tasks/*", 
          "datasources/general-hr-documents"
        ]
      }
    ]
  }
}
```

