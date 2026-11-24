from  typing import  List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
    for idx, elem in enumerate(numbers, 0):
        for  idx2, elem2 in  enumerate(numbers, 0):
            if  idx != idx2:
                distance=abs(elem-elem2)
                if threshold > distance:
                    return True

    return  False