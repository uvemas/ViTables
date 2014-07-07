import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

import nose.tools as nt

import vitables.calculator.calculator as vtc


class TestCalculator:
    """Test calculator functionality."""

    def test_extract_identifiers(self):
        """Test function that extract marked identifiers from an expression."""
        empty_set = vtc.extract_identifiers('')
        nt.assert_true(len(empty_set) == 0)
        nt.assert_equal(set(['$data']), vtc.extract_identifiers('$data'))
        nt.assert_equal(set(['$data']), vtc.extract_identifiers('+$data*'))
        nt.assert_equal(set(['$data']),
                        vtc.extract_identifiers('+$data*$data'))
        nt.assert_equal(set(['$data', '$data1']),
                        vtc.extract_identifiers('+$data*$data1 + test'))
        nt.assert_equal(set(['$data', '$test.data1']),
                        vtc.extract_identifiers('+$data*$test.data1 + test'))
