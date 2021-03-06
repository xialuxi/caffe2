# Copyright (c) 2016-present, Facebook, Inc.
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
##############################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from caffe2.python import core
from hypothesis import given
import caffe2.python.hypothesis_test_util as hu
import hypothesis.strategies as st
import numpy as np


class TestPackRNNSequenceOperator(hu.HypothesisTestCase):

    @given(n=st.integers(0, 10), k=st.integers(1, 5),
           dim=st.integers(1, 5), **hu.gcs_cpu_only)
    def test_pack_rnn_seqence(self, n, k, dim, gc, dc):
        lengths = np.random.randint(k, size=n).astype(np.int32) + 1
        values = np.random.rand(sum(lengths), dim).astype(np.float32)

        def pack_op(values, lengths):
            T = max(lengths) if any(lengths) else 0
            N = lengths.size
            output = np.zeros((T, N) + values.shape[1:]).astype(np.float32)
            offset = 0
            for c in range(N):
                for r in range(lengths[c]):
                    output[r][c] = values[offset + r]
                offset += lengths[c]
            return [output]

        op = core.CreateOperator(
            'PackRNNSequence',
            ['values', 'lengths'],
            'out'
        )

        # Check against numpy reference
        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[values, lengths],
            reference=pack_op,
        )
        # Check over multiple devices
        self.assertDeviceChecks(dc, op, [values, lengths], [0])
        # Gradient check
        self.assertGradientChecks(gc, op, [values, lengths], 0, [0])

    @given(n=st.integers(0, 10), k=st.integers(2, 5),
           dim=st.integers(1, 5), **hu.gcs_cpu_only)
    def test_unpack_rnn_seqence(self, n, k, dim, gc, dc):
        lengths = np.random.randint(k, size=n).astype(np.int32) + 1
        T = max(lengths) if any(lengths) else 0
        N = lengths.size
        values = np.random.rand(T, N, dim).astype(np.float32)

        def unpack_op(values, lengths):
            M = sum(lengths)
            output = np.zeros((M,) + values.shape[2:]).astype(np.float32)
            N = lengths.size
            offset = 0
            for c in range(N):
                for r in range(lengths[c]):
                    output[offset + r] = values[r][c]
                offset += lengths[c]
            return [output]

        op = core.CreateOperator(
            'UnpackRNNSequence',
            ['values', 'lengths'],
            'out'
        )

        # Check against numpy reference
        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[values, lengths],
            reference=unpack_op,
        )
        # Check over multiple devices
        self.assertDeviceChecks(dc, op, [values, lengths], [0])
        # Gradient check
        self.assertGradientChecks(gc, op, [values, lengths], 0, [0])


if __name__ == "__main__":
    import unittest
    unittest.main()
