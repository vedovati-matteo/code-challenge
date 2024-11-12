import pytest
import json
import os
from src.extractor import GoogleCarouselExtractor, extract_from_file
from src.exceptions import CarouselNotFoundError, ListNameNotFoundError

@pytest.fixture
def files_path():
    """Return path to the files directory."""
    # Assuming the 'files' directory is at the root level of the project
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files')

@pytest.fixture
def load_html():
    def _load_html(filename: str) -> str:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files', filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return _load_html

@pytest.fixture
def expected_array():
    def _expected_array(filename: str) -> str:
        """Load the expected array from the files directory."""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files', filename)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return _expected_array


def assert_dicts_equal(result, expected):
    for key, expected_list in expected.items():
        assert key in result, f"Key '{key}' not found in result"
        result_list = result[key]
        
        # Check that both lists have the same length
        assert len(result_list) == len(expected_list), f"List length mismatch for key '{key}'"

        # Check each dictionary in the list
        for i, (expected_item, result_item) in enumerate(zip(expected_list, result_list)):
            for field in expected_item:
                # Skip 'image' field for special check
                if field == "image":
                    expected_image = expected_item.get("image")
                    result_image = result_item.get("image")
                    assert (expected_image is None and result_image is None) or \
                           (isinstance(expected_image, str) and isinstance(result_image, str)), \
                           f"Image field mismatch at key '{key}', index {i}"
                else:
                    assert expected_item[field] == result_item[field], \
                           f"Mismatch at key '{key}', index {i}, field '{field}'"



def test_van_gogh_extraction(files_path, expected_array):
    """Test extraction of Van Gogh paintings carousel."""
    file_path = os.path.join(files_path, 'van-gogh-paintings.html')
    expected = expected_array('expected-array.json')
    
    extractor = GoogleCarouselExtractor(file_path)
    result = extractor.extract()
    
    assert_dicts_equal(result, expected)
    assert 'artworks' in result
    assert len(result['artworks']) > 0
    
    # Test structure of first item
    first_item = result['artworks'][0]
    assert all(key in first_item for key in ['name', 'extensions', 'link', 'image'])
    assert isinstance(first_item['extensions'], list)

def test_other_carousels(files_path):
    """Test extraction works with other carousel pages."""
    # Get all HTML files except van-gogh-paintings.html
    html_files = [f for f in os.listdir(files_path) 
                  if f.endswith('.html') and f not in ('van-gogh-paintings.html', 'invalid_file.html', 'missing_list_name.html')]
    
    for html_file in html_files:
        file_path = os.path.join(files_path, html_file)
        extractor = GoogleCarouselExtractor(file_path)
        result = extractor.extract()
        
        # Basic structure validation
        assert len(result) == 1  # Should have one key (list name)
        list_name = next(iter(result))  # Get the first (and only) key
        items = result[list_name]
        assert isinstance(items, list)
        assert len(items) > 0
        
        # Validate item structure
        for item in items:
            assert 'name' in item
            assert 'extensions' in item
            assert 'link' in item
            assert 'image' in item
            assert isinstance(item['extensions'], list)

def test_invalid_html(files_path):
    """Test handling of invalid HTML."""
    file_path = os.path.join(files_path, 'invalidfile.html')
    
    with pytest.raises(CarouselNotFoundError):
        extractor = GoogleCarouselExtractor(file_path)
        extractor.extract()


def test_missing_list_name(files_path):
    """Test handling of missing list name."""
    file_path = os.path.join(files_path, 'missing_list_name.html')
    
    with pytest.raises(ListNameNotFoundError):
        extractor = GoogleCarouselExtractor(file_path)
        extractor.extract()


def test_file_extraction(files_path):
    """Test extraction from file."""
    file_path = os.path.join(files_path, 'van-gogh-paintings.html')
    result = extract_from_file(file_path)
    
    # Verify it's valid Dict
    assert isinstance(result, dict)
    assert len(result) > 0