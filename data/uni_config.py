import logging
import sys

# Input and output file paths
UNC_FILE = './UNC CAR-T Data_JHU_AI_11.22.24_original.csv'
JHU_FILE = './AI data JH only 9-30-24 CAR3-15-24 LFU7-15-24_original.csv'
OUTPUT_FILE = './unified_clinical_data.csv'
LOG_FILE = './logs/unify_datasets.log'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)