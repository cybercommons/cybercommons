Install Remote Workers
======================

cyberCommons can scale horizontally by allowing remote workers to take on tasks and execute them on remote systems. The following describes how to setup a remote [Celery](http://www.celeryproject.org/) worker for use with cyberCommons. Celery is focused on real-time operation, but supports scheduling as well.

The execution units, called tasks, are executed concurrently on a single or more worker servers using multiprocessing, Eventlet, or gevent. Tasks can execute asynchronously (in the background) or synchronously (wait until ready).

## Requirements

* PIP - [Install](https://packaging.python.org/install_requirements_linux/#installing-pip-setuptools-wheel-with-linux-package-managers)
* Copies of client certificates and credentials to communicate with central cyberCommons server:
  - MongoDB
    - dc_config/ssl/backend/client/mongodb.pem
    - dc_config/ssl/testca/cacert.pem
  - RabbitMQ
    - dc_config/ssl/backend/client/key.pem
    - dc_config/ssl/backend/client/cert.pem
    - dc_config/ssl/testca/cacert.pem
* RabbitMQ and MongoDB ports are open by default:
  - RabbitMQ port 5671
  - MongoDB port 27017

## Install Celery

1. Create virtual environment and activate

    ```sh
    python -m venv virtpy
    source virtpy/bin/activate
    ```

1. Install Celery
    
    ```sh
    (virtpy) $ pip install Celery
    ```


## Configuration
### Get Config Files and Certificates

1. Download example celeryconfig.py and requirements.txt

    ```sh
    wget https://raw.githubusercontent.com/cybercommons/cybercommons/master/docs/pages/files/celeryconfig.py
    ```
1. Create SSL directory and copy cyberCommon's client certificates

    ```sh
    mkdir ssl
    cp mongodb.pem ssl/
    cp key.pem ssl/
    cp cert.pem ssl/
    cp cacert.pem ssl/
    ```
1. Configure celeryconfig.py to point to client certificates and use corresponding credentials (values in this example between "<" and ">" need to be updated to match your cyberCommon's configuration. Do not include the "<" and ">" characters.)

    ```sh
    broker_url = 'amqp://<username>:<password>@<broker_host>:<broker_port>/<broker_vhost>'
    broker_use_ssl = {
        'keyfile': 'ssl/key.pem',
        'certfile': 'ssl/cert.pem',
        'ca_certs': 'ssl/cacert.pem',
        'cert_reqs': ssl.CERT_REQUIRED
    }


    result_backend = "mongodb://<username>:<password>@<mongo_host>:<mongo_port>/?ssl=true&tlsCAFile=ssl/cacert.pem>&tlsCertificateKeyFile=mongodb.pem>"

    mongodb_backend_settings = {
        "database": "<application_short_name>",
        "taskmeta_collection": "tombstone"
    }
    ```

### Configure Tasks

1. Update requirements.txt to include desired libraries and task handlers.
1. Update celeryconfig.py to import task handlers that have been included in requirements file.
 
    ```sh
    imports = ("cybercomq", "name_of_additional_task_handler_library", )
    ```

1. Install requirements

    ```sh
    (virtpy) $ pip install -r requirements.txt
    ```

### Launch Celery worker

1. Run in foreground. See [Celery Worker Documentation](https://docs.celeryproject.org/en/stable/reference/cli.html#celery-worker) for more information.

    ```sh
    celery worker -Q remote -l INFO -n dev-hostname
    ```
