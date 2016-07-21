import Image

class AbstractArenaImage:
    def __init__ (self):
        self.width = 600
        self.height = 600
        self.difference_threshold = 35

    def valid_pixel (self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height
    
    def different_pixel (self, x, y, jpgfile_data1, jpgfile_data2):
        if self.valid_pixel (x, y):
            index = x + y * self.width
            pixel1 = jpgfile_data1 [index]
            pixel2 = jpgfile_data2 [index]
            # gray image
            if abs (pixel1 [0] - pixel2 [0]) >= self.difference_threshold:
                return 1
            else:
                return 0
        else:
            return 0

class CircularArenaImage (AbstractArenaImage):
    """
    Contains details about the background image and the iteration images.  This has to be done every time we switch bees.
    """
    def __init__ (self):
        AbstractArenaImage.__init__ (self)

    def ask_image_properties (self):
        print "\n\n* ** Arena Image Information ** *"
        print "Check the background image and enter the following information"
        ok = False
        while not ok:
            try:
                self.casu_x = int (raw_input ("horizontal coordinate of center of active CASU? "))
                self.casu_y = int (raw_input ("vertical coordinate of center of active CASU? "))
                self.arena_radius = int (raw_input ("radius of arena (in pixels)? "))
                self.aggregation_area_radius = int (raw_input ("radius of aggregation radius (in pixels)? "))
#                self.difference_threshold = int (raw_input ("gray level difference threshold to use? "))
                ok = True
            except ValueError:
                print "Enter image values again"
                ok = False

    def bee_percentage_around_casus (self, jpgfile_data1, jpgfile_data2):
        """
        Compute how many bees are around the active CASU.

        One of the parameters should be the background image, and the other should be an iteration step image.

        Only pixels that are different are taken into account.

        Returns a 2-tuple with bee percentage around active CASU and with bee percentage around passive CASU.
        """
        bee_area = 0
        square_radius = self.arena_radius ** 2
        for x in xrange (-self.arena_radius, self.arena_radius + 1, 1):
            for y in xrange (-self.arena_radius, self.arena_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    bee_area += self.different_pixel (x + self.casu_x, y + self.casu_y, jpgfile_data1, jpgfile_data2)
        active_area = 0
        square_radius = self.aggregation_area_radius ** 2
        for x in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
            for y in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    active_area += self.different_pixel (x + self.casu_x, y + self.casu_y, jpgfile_data1, jpgfile_data2)
        if bee_area == 0:
            return (-1, -1)
        else:
            return ((100.0 * active_area) / bee_area, -1)

    def moving_bees_around_casus (self, jpgfile_data1, jpgfile_data2):
        """
        Compute how many bees are moving aroung the active and passive CASUs.

        Both parameters should be iteration step images.

        Only pixels that are different are taken into account.
        """
        active_area = 0
        square_radius = self.aggregation_area_radius ** 2
        for x in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
            for y in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    active_area += self.different_pixel (x + self.casu_x, y + self.casu_y, jpgfile_data1, jpgfile_data2)
        return (active_area / self.aggregation_area_radius, -1)

    def create_measure_area_image (self, imgpath):
        jpgfile = Image.open (imgpath + "Background.jpg")
        data = jpgfile.getdata ()
        change = [p for p in data]
        
        square_radius = self.aggregation_area_radius ** 2
        for x in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
            for y in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    rx = x + self.casu_x
                    ry = y + self.casu_y
                    index = rx + ry * self.width
                    pixel = change [index]
                    change [index] = (pixel [0], 255, pixel [2])
        jpgfile.putdata (change)
        jpgfile.save (imgpath + "Measured-Area.jpg")
        
    def __str__ (self):
        return "x"




class StadiumArenaImage (AbstractArenaImage):
    """
    Contains details about the background image and the iteration images.  This has to be done every time we switch bees.
    
    The stadium arena has two CASUs.
    """
    def __init__ (self):
        AbstractArenaImage.__init__ (self)

    def ask_image_properties (self):
        print "\n\n* ** Arena Image Information ** *"
        print "Check the background image and enter the following information"
        ok = False
        while not ok:
            try:
                self.arena_left = int (raw_input ("leftmost (min) pixel of the arena? "))
                self.arena_right = int (raw_input ("rightmost (max) pixel of the arena? "))
                self.arena_top = int (raw_input ("topmost (min) pixel of the arena? "))
                self.arena_bottom = int (raw_input ("bottommost (max) pixel of the arena? "))
                self.casu_active_x = int (raw_input ("horizontal coordinate of center of active CASU? "))
                self.casu_active_y = int (raw_input ("vertical coordinate of center of active CASU? "))
                self.casu_passive_x = int (raw_input ("horizontal coordinate of center of passive CASU? "))
                self.casu_passive_y = int (raw_input ("vertical coordinate of center of passive CASU? "))
                self.aggregation_area_radius = int (raw_input ("radius of aggregation radius (in pixels)? "))
#                self.difference_threshold = int (raw_input ("gray level difference threshold to use? "))
                ok = True
            except ValueError:
                print "Enter image values again"
                ok = False

    def bee_percentage_around_casus (self, jpgfile_data1, jpgfile_data2):
        """
        Compute how many bees are around the active and passive CASUs.

        One of the parameters should be the background image, and the other should be an iteration step image.

        Only pixels that are different are taken into account.

        Returns a 2-tuple with bee percentage around active CASU and with bee percentage around passive CASU.
        """
        bee_area = 0
        for x in xrange (self.arena_left, self.arena_right + 1, 1):
            for y in xrange (self.arena_top, self.arena_bottom + 1, 1):
                bee_area += self.different_pixel (x, y, jpgfile_data1, jpgfile_data2)
        active_area = 0
        passive_area = 0
        square_radius = self.aggregation_area_radius ** 2
        for x in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
            for y in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    active_area += self.different_pixel (x + self.casu_active_x, y + self.casu_active_y, jpgfile_data1, jpgfile_data2)
                    passive_area += self.different_pixel (x + self.casu_passive_x, y + self.casu_passive_y, jpgfile_data1, jpgfile_data2)
        if bee_area == 0:
            return (-1, -1)
        else:
            return ((100.0 * active_area) / bee_area, (100.0 * passive_area) / bee_area)

    def moving_bees_around_casus (self, jpgfile_data1, jpgfile_data2):
        """
        Compute how many bees are moving aroung the active and passive CASUs.

        Both parameters should be iteration step images.

        Only pixels that are different are taken into account.
        """
        active_area = 0
        passive_area = 0
        square_radius = self.aggregation_area_radius ** 2
        for x in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
            for y in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    active_area += self.different_pixel (x + self.casu_active_x, y + self.casu_active_y, jpgfile_data1, jpgfile_data2)
                    passive_area += self.different_pixel (x + self.casu_passive_x, y + self.casu_passive_y, jpgfile_data1, jpgfile_data2)
        return (active_area / self.aggregation_area_radius, passive_area / self.aggregation_area_radius)

    def different_pixel (self, x, y, jpgfile_data1, jpgfile_data2):
        index = x + y * self.width
        pixel1 = jpgfile_data1 [index]
        pixel2 = jpgfile_data2 [index]
        # gray image
        if abs (pixel1 [0] - pixel2 [0]) >= self.difference_threshold:
            return 1
        else:
            return 0

    def pixel_count_difference (self, jpgfile_data1, jpgfile_data2, active_casu):
        """
        Return the pixel count difference between the two images but only for the pixels around the given casu.

        This function is used to compute how many bees are moving by comparing two consecutive images.

        :param: jpgfile_data1 the image data from one iteration step

        :param: jpgfile_data2 the image data from anoter iteration step
        """
        result = 0
        square_radius = self.aggregation_area_radius ** 2
        for x in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
            for y in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    if active_casu:
                        rx = x + self.casu_active_x
                        ry = y + self.casu_active_y
                    else:
                        rx = x + self.casu_passive_x
                        ry = y + self.casu_passive_y
                    index = rx + ry * self.width
                    pixel1 = jpgfile_data1 [index]
                    pixel2 = jpgfile_data2 [index]
                    # gray image
                    if abs (pixel1 [0] - pixel2 [0]) >= self.difference_threshold:
                        result += 1
        result = result / self.aggregation_area_radius
        return result

    def create_measure_area_image (self, imgpath):
        jpgfile = Image.open (imgpath + "Background.jpg")
        data = jpgfile.getdata ()
        change = [p for p in data]
        
        square_radius = self.aggregation_area_radius ** 2
        for x in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
            for y in xrange (-self.aggregation_area_radius, self.aggregation_area_radius + 1, 1):
                square_dist = x ** 2 + y ** 2
                if square_dist <= square_radius:
                    rx = x + self.casu_active_x
                    ry = y + self.casu_active_y
                    index = rx + ry * self.width
                    pixel = change [index]
                    change [index] = (pixel [0], 255, pixel [2])
                    rx = x + self.casu_passive_x
                    ry = y + self.casu_passive_y
                    index = rx + ry * self.width
                    pixel = change [index]
                    change [index] = (255, pixel [1], pixel [2])
        jpgfile.putdata (change)
        jpgfile.save (imgpath + "Measured-Area.jpg")
        
    def __str__ (self):
        return "x"





if __name__ == "__main__":
    im = ArenaImage ()
    im.create_measure_area_image ("./")
    backdata = Image.open ("Background.jpg").getdata ()
    iterdata = Image.open ("iterationimage_5_0041.jpg").getdata ()
    print im.pixel_count_difference (backdata, iterdata, True)
    
