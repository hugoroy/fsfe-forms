# forms API

[![Build Status](https://drone.fsfe.org/api/badges/FSFE/forms/status.svg)](https://drone.fsfe.org/FSFE/forms)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

The forms API, available under <https://forms.fsfe.org> can be used to send
form data from a web page submission, via email, to somewhere else. The API
is highly configurable and can be adapted for a wide variety of situations
in which you need to send emails from a web page, either with or without
double opt-in.

Each application which intends to use this service must be registered in
the API configuration, which is available in `src/configuration/applications.json`.

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [API](#api)
- [Contribute](#contribute)
- [License](#license)

## Install

It is not expected that you install the forms API code yourself, but if you
choose to do so, you will be expected to install and run both the worker and
web app. Both need access to a Redis. The web app takes care of the frontend
API, whereas the worker is responsible for actually sending out emails.

To setup the environment:

```
$ export REDIS_HOST=redishostname
$ export REDIS_PORT=redispost
$ export REDIS_PASSWORD=redispassword  # if required
$ pip install -r requirements.txt
```

You can then run the web app with:

```
src/$ gunicorn -b 0.0.0.0:8080 wsgi:application
```

This will run the web application on port 8080 on the default network
interface. Starting the background worker is done with:

```
src/$ python worker.py worker -l info
```

## Usage

### Sending a ticket to our ticket system

You're writing a page in which you would like to create a form where
submission of that form creates a ticket in our ticket system. There's
no need for an opt-in for this, and we don't want to store information
outside of the ticket system.

The application configuration could look like this:

```json
  "totick2": {
    "ratelimit": 500,
    "to": [ "contact@fsfe.org" ],
    "subject": "Registration of event from {{ participant_name }}",
    "include_vars": true,
    "redirect": "http://fsfe.org",
    "template": "totick2-template",
    "required_vars": ["participant_name"],
    "headers": {
      "X-OTRS-Queue": "Promo"
    }
  },
```

The template configuration could look like this:

```json
  "totick2-template": {
    "filename": "totick2-template.html",
    "required_vars": ["country", "message", "participant_name"],
    "headers": {
      "X-PARTICIPANT-NAME": "{{ participant_name }}"
    }
  }
```

The HTML form could look like this:

```html
<form method="POST" action="https://forms.fsfe.org/email">
  <!-- Parameter "appid" is required to identify what application configuration is used to send email -->
  <input type="hidden" name="appid" value="totick2">
  Your name: <input type="text" name="participant_name">
  Your e-mail: <input type="email" name="from" />
  Your country: <input type="text" name="country" />
  Your message: <input type="text" name="message" />
</form>
```

And finally, the template:

```
Hi!

My name is {{ participant_name }}.
I'm from {{ country }} and would like you to know:

  {{ message }}
```

### Signing an open letter
In this case, we're publishing an open letter which we invite people to
sign. We want to store information about who has signed the open letter,
and we want a double opt-in of their email address so we know we have
a working e-mail. We don't want to include anyone in the list without them
having confirmed.

The configuration could look like this:

```json
  "tosign": {
    "ratelimit": 500,
    "from": "admin@fsfe.org",
    "to": [ "campaignowner@fsfe.org" ],
    "subject": "New signatory to open letter",
    "include_vars": true,
    "redirect": "http://fsfe.org",
    "template": "tosign-template",
    "store": "/store/campaign2.json",
    "confirm": true,
  },
```

The template configuration could look like this:

```json
  "tosign-template": {
    "filename": "tosign-template.html",
    "required_vars": ["name", "confirm", "country"]
  }
```

The HTML form could look like this:

```html
<form method="POST" action="https://forms.fsfe.org/email">
  <!-- Parameter "appid" is required to identify what application configuration is used to send email -->
  <input type="hidden" name="appid" value="tosign">
  Please sign our open letter here!

  Your name: <input type="text" name="name" />
  Your e-mail: <input type="email" name="confirm" />
  Your country: <input type="text" name="country" />
</form>
```

And finally, the template:

```
Hi!

I support your work and sign your open letter about X!

  {{ name }} <{{ confirm }}> from {{ country }}.
```

When someone submits the form, a mail will first be sent to the address
given. The e-mail will have the following form:

```
You've requested the following e-mail to be sent on your behalf.

"Hi!

I support your work and sign your open letter about X!

  John Doe <john@example.com> from Switzerland.
"

To confirm, please click the following link. If you do not click
this link to confirm, your mail will not be sent.

https://forms.fsfe.org/confirm?id=randomnumber
```

No information will be stored, and no email sent to the To address before
the user clicks that URL. When the URL is clicked, the email will be sent
to <campaignowner@fsfe.org> as given in the configuration, and a JSON
file `/store/campaign2.json` will be created with the following content:

```json
{"from": "admin@fsfe.org", "to": ["campaignowner@fsfe.org"], "subject": "New signatory to open letter",
"content": "Hi!\n\nI support your work and sign your open letter about X!\n\n  John Doe <john@example.com> from Switzerland.\n",
"reply-to": null,
"include_vars": {"name": "John Doe", "confirm": "john@example.com", "country": "Switzerland"}}
```



## API

### POST/GET https://forms.fsfe.org/email

This will trigger the sending of an email, potentially with a double opt-in
according to the configuration. The following parameters are supported:

 * appid (required)
 * from
 * to
 * replyto
 * subject
 * content
 * template
 * confirm (required for some appid)

### GET https://forms.fsfe.org/confirm

This will confirm an e-mail address if using double opt-in. The following
parameters are supported:

 * confirm (required)

The value for confirm is generated automatically by the forms system. You
should never need to generate this URL yourself.

### Supported parameters for each registered application user

Most of the parameters which are available for an application can be set
*either* in the API configuration, or in the GET request when calling the
API. If a parameter is specified in the API configuration, this takes
precendence. So for instance, if the API configuration sets the To
address as `nobody@example.com`, then even if the request includes
`to=foo@example.com`, this will be ignored, and the To address set
according to the API configuration.

These are the available parameters for configuration or request:

 * **from**: sets an explicit From address on emails sent. Could contain variables
 * **to**: one or more recipients, explicit To address. Could contain variables
 * **replyto**: sets an explicit Reply-To header on emails sent
 * **subject**: sets the Subject of an email. Could contain variables
 * **content**: sets the content (plain text) of an email. Could contain variables
 * **template**: defines which template configuration will be used to provide content. Could contain variables

If both **content** and **template** is set, then **template** will be used
instead.

The following parameters are available only in the API configuration file:

 * **ratelimit**: controls the number of emails allowed to be sent per hour
 * **include_vars**: if set to true, then any extra variables provided in a GET request will be made available to the template when rendering an email
 * **store**: if set to a filename, then information about emails sent will be stored in this file. This will not inclue emails which have not been confirmed (if double opt-in is in use).
 * **confirm**: if set to true, then no email is sent without an explicit confirmation of a suitable e-mail address. The email to confirm should be passed in the **confirm** parameter of the GET request (see later)
 * **redirect**: address to redirect the user to after having accepted and processed a request
 * **redirect-confirmed**: address to redirect the user to after the user has confirmed their email (if using confirm==true)
 * **required_vars**: an array with parameter names that has to be presented in request parameters
 * **headers**: a key-value dictionary that should be included to email as headers. Values could contain variables
 * **confirmation-template**: name of a template defined in templates config that will be used as confirmation email. For confirmation emails already provided 2 variables: "confirmation_url" and "content". Content is the rendered email that will be sent after confirmation
 * **confirmation-subject**: custom subject for confirmation email. Could contain variables

## Contribute
We'd love to get feedback on these practices, ideally in the form
of pull requests which we can discuss around. To be able to contribute
in this way, you need an account on `git.fsfe.org`, which you can
get by going to our [account creation page](https://fsfe.org/fellowship/ams/index.php?ams=register). This will sign you up for a volunteer account with the FSFE.

Once you've registered, your account needs to be activated. Just shoot a mail to <contact@fsfe.org> or directly to <jonas@fsfe.org> saying you've registered and would like to be activated. As soon as your account is activated, you can set a username and proceed to login to `git.fsfe.org`.

We also accept and appreciate feedback by creating issues in the project
(requires the same account creation), or by sending e-mail to, again,
<contact@fsfe.org> or <jonas@fsfe.org>.

## License
This software is copyright 2017 by the Free Software Foundation Europe e.V.
and licensed under the GPLv3 license. For details see the "LICENSE" file in
the top level directory of https://git.fsfe.org/fsfe/forms/

