def add_decorator_to_methods(decorator):
    """
    This function takes a decorator as input and returns a decorator wrapper function. The decorator wrapper function takes a class as input and decorates all the methods of the class by applying the input decorator to each method.

    Parameters:
        - decorator: A decorator function that will be applied to the methods of the input class.

    Returns:
        - decorator_wrapper: A function that takes a class as input and decorates all the methods of the class by applying the input decorator to each method.
    """
    def decorator_wrapper(cls):
        # 获取要装饰的类的所有方法
        methods = [attr for attr in dir(cls) if callable(getattr(cls, attr)) and not attr.startswith("_")]

        # 为每个方法添加装饰器
        for method in methods:
            setattr(cls, method, decorator(getattr(cls, method)))

        return cls
    return decorator_wrapper