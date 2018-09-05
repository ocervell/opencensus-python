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

import unittest

import mock

from opencensus.trace.ext.httplib2 import trace
from opencensus.trace.propagation import trace_context_http_header_format


class Test_httplib2_trace(unittest.TestCase):

    def tearDown(self):
        from opencensus.trace import execution_context

        execution_context.clear()

    def test_trace_integration(self):
        mock_wrap_request = mock.Mock()
        mock_httplib2 = mock.Mock()

        wrap_request_result = 'wrap request result'
        mock_wrap_request.return_value = wrap_request_result

        mock_request_func = mock.Mock()
        mock_request_func.__name__ = 'request'
        setattr(mock_httplib2.Http, 'request', mock_request_func)

        patch_wrap_request = mock.patch(
            'opencensus.trace.ext.httplib2.trace.wrap_httplib2_request',
            mock_wrap_request)
        patch_httplib2 = mock.patch(
            'opencensus.trace.ext.httplib2.trace.httplib2',
            mock_httplib2)

        with patch_wrap_request, patch_httplib2:
            trace.trace_integration()

        self.assertEqual(
            getattr(mock_httplib2.Http, 'request'),
            wrap_request_result)

    def test_wrap_httplib2_request(self):
        # Mock 'span'
        mock_span = mock.Mock()
        mock_span.span_id = '1234'
        patch_attr = mock.patch(
            'opencensus.trace.ext.httplib2.trace.'
            'execution_context.get_opencensus_attr',
            return_value=mock_span.span_id)

        # Mock 'tracer' object
        mock_tracer = MockTracer(mock_span)
        patch_tracer = mock.patch(
            'opencensus.trace.ext.requests.trace.execution_context.'
            'get_opencensus_tracer',
            return_value=mock_tracer)

        # Mock 'httplib2.Response' object
        mock_resp = mock.Mock()
        mock_resp.status = '200'

        # Mock `httplib2.request` function
        mock_request_func = mock.Mock()
        mock_request_func.__name__ = 'request'
        mock_request_func.return_value = [mock_resp, ""]

        # Mock 'httplib2.request' attributes
        method = 'GET'
        url = 'http://localhost:8080'
        body = None
        status_code = '200'
        headers = {}
        expected_attributes = {
            '/http/url': url,
            '/http/method': method,
            '/http/status_code': status_code
        }
        expected_name = '[httplib2]request'

        # Call wrapped 'httplib2.request'
        wrapped = trace.wrap_httplib2_request(mock_request_func)
        with patch_tracer, patch_attr:
            wrapped(mock.Mock(), url, method, body=body, headers=headers)

        # Tests
        self.assertEqual(
            expected_attributes,
            mock_tracer.span.attributes)
        self.assertEqual(expected_name, mock_tracer.span.name)


class MockTracer(object):
    def __init__(self, span=None):
        self.span = span
        self.propagator = (
            trace_context_http_header_format.TraceContextPropagator()
        )

    def current_span(self):
        return self.span

    def start_span(self):
        span = mock.Mock()
        span.attributes = {}
        span.context_tracer = mock.Mock()
        span.context_tracer.span_context = mock.Mock()
        span.context_tracer.span_context.trace_id = '123'
        span.context_tracer.span_context.span_id = '456'
        span.context_tracer.span_context.tracestate = None
        self.span = span
        return span

    def end_span(self):
        pass

    def add_attribute_to_current_span(self, key, value):
        self.span.attributes[key] = value
