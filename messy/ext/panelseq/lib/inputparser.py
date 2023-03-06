
# manual parser for regions (BED-like) and variant (POSITION) streams
#

import pandas as pd
import io


def text_to_dataframe(text, header):
    text = text.strip()
    if not (text.startswith('CHROM') or text.startswith('CODE')):
        # add standard header as above
        text = header + text
    buf = io.StringIO(text)
    return pd.read_table(buf, sep='\t')


def parse_regions(text, header="CODE\tCHROM\tBEGIN\tEND\n"):
    return text_to_dataframe(text, header)


def parse_variants(text, header="CODE\tCHROM\tPOSITION\n"):
    return text_to_dataframe(text, header)

# EOF
