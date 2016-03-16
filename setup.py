from distutils.core import setup
import setup_translate


setup(name = 'enigma2-plugin-extensions-tmbd',
		version='6.9',
		author='Dimitrij',
		author_email='dima-73@inbox.lv',
		packages=['Extensions.TMBD.src', 'Extensions.TMBD.profile', 'Extensions.TMBD.tmdb3'],
		package_data={'Extensions.TMBD': ['*.png', 'ir/*.png']},
		description = 'Search the internet bases themoviedb.org/kinopoisk.ru',
		cmdclass = setup_translate.cmdclass,
	)
