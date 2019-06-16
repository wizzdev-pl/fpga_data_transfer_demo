import subprocess
import os
import sys
import logging

current_script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_script_dir, '../'))

from demo_src.status_logger import StatusBarLogHandler

from gui.main_window import MainWindow

from PySide2.QtWidgets import QApplication

logger = logging.getLogger("Status bar logger")


def create_moc(dir_path, file_name):
    input_file = os.path.join(dir_path, file_name)
    output_file = os.path.join(dir_path, 'moc_' + (os.path.splitext(file_name)[0]) + '.py')

    if os.path.isfile(output_file):
        ui_file_modification_time = os.path.getmtime(input_file)
        moc_file_modification_time = os.path.getmtime(output_file)
        if moc_file_modification_time > ui_file_modification_time:
            print('Skipping mocking of file {}, older than moc file'.format(input_file))
            return

    try:
        print('Remove old moc file: %s' % output_file)
        os.remove(output_file)
    except OSError:
        pass

    command = 'pyside2-uic ' + input_file + ' -o ' + output_file + ' -x'
    print('Mocking file %s...' % input_file)

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output_bin, err_bin) = process.communicate(timeout=10)
    return_code = process.returncode
    if return_code is not 0:
        raise Exception('Mocing ui file failed! (' + file_name + '). '
                         'cout: ' + str(output_bin) + '. cerr: ' + str(err_bin))

def create_mocs():
    for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
        for file in files:
            if file.endswith(".ui"):
                create_moc(root, file)
    print('Mocking finished!')

def setup_logging():
    logger = logging.getLogger("Status bar logger")
    status_bar_logger = StatusBarLogHandler()
    status_bar_logger.setup_for_logging()


def run_app():
    app = QApplication()
    main_window = MainWindow()
    main_window.show()
    app.exec_()


if __name__ == "__main__":
    setup_logging()
    create_mocs()
    run_app()

