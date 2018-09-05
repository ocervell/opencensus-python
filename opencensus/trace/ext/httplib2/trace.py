# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys
import httplib2

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module

log = logging.getLogger(__name__)

MODULE_NAME = 'httplib2'
HTTPLIB2_REQUEST_FUNC = 'request'

HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']


def trace_integration(tracer=None):
    """Wrap the `httplib2` method to trace."""
    log.info('Integrated module: {}'.format(MODULE_NAME))

    # Wrap the httplib request function
    request_func = getattr(httplib2.Http, HTTPLIB2_REQUEST_FUNC)
    wrapped_request = wrap_httplib2_request(request_func)
    setattr(httplib2.Http, request_func.__name__, wrapped_request)

def wrap_httplib2_request(request_func):
    """Wrap the httplib2 request function to trace.

    Args:
        request_func (function): The `httplib2` function to wrap.
    """

    def call(self, url, *args, **kwargs):
        _tracer = execution_context.get_opencensus_tracer()
        _span = _tracer.start_span()
        _span.span_kind = span_module.SpanKind.CLIENT
        _span.name = '[httplib2]{}'.format(request_func.__name__)

        # Add attributes to span
        method = kwargs.get('method', 'GET')
        _tracer.add_attribute_to_current_span(HTTP_URL, url)
        _tracer.add_attribute_to_current_span(HTTP_METHOD, method)

        # Update header context
        try:
            headers = headers.copy()
            headers.update(_tracer.propagator.to_headers(
                _span.context_tracer.span_context))
        except Exception:  # pragma: NO COVER
            pass

        # Fire request and get response
        (r, data) = request_func(self, url, *args, **kwargs)

        # Add the status code to attributes
        _tracer.add_attribute_to_current_span(HTTP_STATUS_CODE, str(r.status))

        # End current span
        _tracer.end_span()

        return r, data

    return call
