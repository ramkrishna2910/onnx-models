from app import update_onnx_cards, update_cards, task_to_value

'''
The following tests verify the functionality of specific components and features within the 
dash app. These tests are tailored to the current layout and structure of the app. Any 
modifications to the app's structure may require corresponding updates to these tests.
'''

def test_update_onnx_cards_search_bar():
    '''
    This tests the functionality of the search bar in the onnx_cards tab.
    Uses a an example search term and ensures that only files that match the search term are 
    displayed.
    '''
    search_term = "resnet50"
    output = update_onnx_cards(None, search_term)
    def check_if_target_exists_header(row, target_term):
        # Get the children of the Row component
        children = row.children

        # Iterate over the children
        for child in children:
            # Extract model name from CardHeader
            text = child.children.children[0].children[0].children
            
            # Check if the target term is present in the extracted text
            if target_term in text:
                return True
        return False
    assert check_if_target_exists_header(output, search_term) is True

def test_update_onnx_cards_filtering():
    '''
    This tests the functionality of the filters in the onnx_cards tab.
    Uses a an example search filter and ensures that only files that match the filter are 
    displayed.
    '''
    filter = "Computer Vision"
    filter_value = task_to_value("Computer Vision")
    output = update_onnx_cards([filter_value], None)
    def check_if_target_exists_body(row, target_term):
        # Get the children of the Row component
        children = row.children

        # Iterate over the children
        for child in children:
            # Extract Model task from CardBody
            text = child.children.children[2].children[0].children
            
            # Check if the target term is present in the extracted text
            if target_term in text:
                return True
        return False
    assert check_if_target_exists_body(output, filter) is True

def test_update_cards_search_bar():
    '''
    This tests the functionality of the search bar in the model cards tab.
    Uses a an example search term and ensures that only files that match the search term are 
    displayed.
    '''
    search_term = "resnet50"
    prev_clicks = next_clicks = 0
    output = update_cards(prev_clicks, next_clicks, search_term, None)
    def check_if_target_exists_header(row, target_term):
        # Get the children of the Row component
        children = row[0].children

        # Iterate over the children
        for child in children:
            # Extract model name from CardHeader
            text = child.children.children[0].children.children
            
            # Check if the target term is present in the extracted text
            if target_term in text:
                return True
        return False
    assert check_if_target_exists_header(output, search_term) is True

def test_update_cards_filtering():
    '''
    This tests the functionality of the filters in the model cards tab.
    Uses a an example search filter and ensures that only files that match the filter are 
    displayed.
    '''
    filter = "Computer Vision"
    filter_value = task_to_value("Computer Vision")
    prev_clicks = next_clicks = 0
    output = update_cards(prev_clicks, next_clicks, None, [filter_value])
    def check_if_target_exists_body(row, target_term):
        # Get the children of the Row component
        children = row[0].children

        # Iterate over the children
        for child in children:
            # Extract Model task from CardBody
            text = child.children.children[1].children[0].children.split(":")[-1].strip()
            
            # Check if the target term is present in the extracted text
            if target_term in text:
                return True
        return False
    assert check_if_target_exists_body(output, filter) is True