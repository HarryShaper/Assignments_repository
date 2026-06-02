from showtools.ShowTools import *

if __name__ == "__main__":
	try:
		app = QtWidgets.QApplication(sys.argv)
		initialize_app = ShowTools()
		app.exec()

	except Exception as error:
		import traceback
		traceback.print_exc()
		input("Press Enter to close...")