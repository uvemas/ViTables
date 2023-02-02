import vitables.calculator.calculator as vtc


class TestCalculator:
    """Test calculator functionality."""

    def test_extract_identifiers(self):
        """Test function that extract marked identifiers from an expression."""
        empty_set = vtc.extract_identifiers('')
        assert len(empty_set) == 0
        assert set(['$data']) == vtc.extract_identifiers('$data')
        assert set(['$data']) == vtc.extract_identifiers('+$data*')
        assert set(['$data']) == vtc.extract_identifiers('+$data*$data')
        assert set(['$data', '$data1']) == vtc.extract_identifiers('+$data*$data1 + test')
        assert set(['$data', '$test.data1']) == vtc.extract_identifiers('+$data*$test.data1 + test')
