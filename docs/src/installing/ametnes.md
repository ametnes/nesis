# Ametnes Platform

The Ametnes Platform helps orchestrate your business applications wherever you host them. This can be in your private
data-center, in AWS, GCP or Azure.

Nesis is available on the Ametnes Platform and can be deployed in your kubernetes cluster wherever you host it.

The first step is to set up your kubernetes cluster as an Ametnes Application Location. See these detailed <a href="https://cloud.ametnes.com/docs/concepts/data-service-location/" target="_blank">instructions</a>.

## Create the service

Log into your Ametnes Cloud console at <a href="https://cloud.ametnes.com/console/signin" target="_blank">here</a>
or sign up <a href="https://cloud.ametnes.com/console/signup" target="_blank">here</a> if you do not have one.

1. Using the **Services** left menu, navigate to the service management dashboard.
2. Click **New Service**.
3. Enter the **__Nesis__** to filter from the list and select **__Create__**
4. In the displayed form, enter the following info.
    1. Enter the **Name**: `Nesis-Service-DSL1` and **Description**: `Nesis-Service-DSL1`.
    2. Select a **Version** from the list.
    3. Select the **Location**.
    4. Set the `OPENAI_API_KEY` and the `HF_TOKEN` keys.
    4. Click `Create`.

## Test connectivity

1. Using the **Services** left menu, navigate to the service management dashboard. Your service should be listed.

    !!! note "Service not showing"
        If your service list is empty, use the filter at the top right corner, to filter for ALL services.

2. After a while, your data service status will change to `ready`.
2. To the right of your service, click the `Admin` button and you will navigate to your service's details page.
3. At the bottom of the page, copy the endpoint of your service as well as your username/key and password.
4. In your browser, paste the URL `https://<your.instance.host.name>/`.
5. You should get a prompt to login.

## Clean up

### Delete all services
1. In your Ametnes Cloud console, navigate to the **Admin** section of each service
2. Delete the service.

