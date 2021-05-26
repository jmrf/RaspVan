import logging

import coloredlogs


def disable_lib_loggers():
    # disable other loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def install_logger(
    logger, level, fmt="%(levelname)-8s %(name)-25s:%(lineno)4d - %(message)-50s"
):
    """ Configures the given logger; format, logging level, style, etc """

    def add_notice_log_level():
        """ Creates a new 'notice' logging level """
        # inspired by:
        # https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility
        NOTICE_LEVEL_NUM = 25
        logging.addLevelName(NOTICE_LEVEL_NUM, "NOTICE")

        def notice(self, message, *args, **kws):
            if self.isEnabledFor(NOTICE_LEVEL_NUM):
                self._log(NOTICE_LEVEL_NUM, message, args, **kws)

        logging.Logger.notice = notice

    # Add an extra logging level above INFO and below WARNING
    add_notice_log_level()

    # More style info at:
    # https://coloredlogs.readthedocs.io/en/latest/api.html
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES.copy()
    field_styles["asctime"] = {}
    level_styles = coloredlogs.DEFAULT_LEVEL_STYLES.copy()
    level_styles["debug"] = {"color": "white", "faint": True}
    level_styles["notice"] = {"color": "cyan", "bold": True}

    coloredlogs.install(
        logger=logger,
        level=level,
        use_chroot=False,
        fmt=fmt,
        level_styles=level_styles,
        field_styles=field_styles,
    )


def configure_logging(logger, level):
    disable_lib_loggers()
    install_logger(logger, level=level)
