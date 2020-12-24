def get_logger(name, **kwargs):
    import logging
    logging.basicConfig(**kwargs)
    log = logging.getLogger(name)
    log.debug(f"start logging '{name}'")
    return log
