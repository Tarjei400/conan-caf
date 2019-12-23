#!/usr/bin/env python

import platform
from bincrafters import build_template_default


def get_shared_option_name():
    return False if platform.system() == 'Windows' else "caf:shared"


if __name__ == "__main__":
    builder = build_template_default.get_builder(pure_c=False,
                                                 shared_option_name=get_shared_option_name())
    builder.run()
