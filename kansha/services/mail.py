# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.Utils import COMMASPACE, formatdate

from nagare import log

from .services_repository import Service


class MailSender(Service):
    load_priority = 10
    config_spec = {
        'activated': 'boolean(default=True)',
        'smtp_host': 'string(default="127.0.0.1")',
        'smtp_port': 'integer(default=25)',
        'default_sender': 'string(default="noreply@email.com")'
    }

    def __init__(self, config_filename, config, error):
        super(MailSender, self).__init__(config_filename, config, error)
        self.host = config['smtp_host']
        self.port = config['smtp_port']
        self.default_sender = config['default_sender']
        self.activated = config['activated']
        if self.activated:
            log.debug(
                'The mail service will connect to %s on port %s' %
                (self.host, self.port)
            )
        else:
            log.warning('The mail service will drop all messages!')

    def _smtp_send(self, from_, to, contents):
        smtp = smtplib.SMTP(self.host, self.port)
        try:
            smtp.sendmail(from_, to, contents)
        except Exception as e:
            log.exception(e)
        finally:
            smtp.close()

    def send(self, subject, to, content, html_content=None, from_='', cc=[], bcc=[],
             type='plain', mpart_type='alternative'):
        """Sends an email

        In:
         - ``subject`` -- email object
         - ``to`` -- To email's list
         - ``content`` --  email content
         - ``from_`` -- email sender
         - ``cc`` --  CC email's list
         - ``bcc`` -- BCC email's list
         - ``type`` --  email type
         - ``mpart_type`` -- email part type

        """
        from_ = from_ if from_ else self.default_sender
        # create the message envelop
        msg = MIMEMultipart(mpart_type)
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['From'] = from_
        msg['To'] = COMMASPACE.join(to)

        if cc:
            msg['Cc'] = COMMASPACE.join(cc)

        # attach the mail content
        charset = 'us-ascii'
        if isinstance(content, unicode):
            content = content.encode('UTF-8')
            charset = 'UTF-8'
        msg.attach(MIMEText(content, type, charset))
        if html_content:
            msg.attach(MIMEText(html_content, 'html', charset))

        # log
        log.info('%s mail:\n  subject=%s\n  from=%s\n  to=%s\n  cc=%s\n  bcc=%s',
                 'sending' if self.activated else 'ignoring', subject, from_, to, cc, bcc)
        log.debug('Mail content:\n' + content)

        # post the email to the SMTP server
        if self.activated:
            self._smtp_send(from_, to + cc + bcc, msg.as_string())
