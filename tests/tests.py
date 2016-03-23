import spotifywrappy
import unittest
from spotifywrappy import wrapper

class TestAlbumMethods(unittest.TestCase):

    def test_get_an_album(self):
    	# Arrange
        sp = wrapper.Spotify(None, None, None, None)
        alubmId = '0sNOF9WDwhWunNAHPD3Baj'

        # Act
        album = sp.get_album(alubmId)

        # Assert
        self.assertEqual(album['name'], "She's So Unusual")

if __name__ == '__main__':
    unittest.main()