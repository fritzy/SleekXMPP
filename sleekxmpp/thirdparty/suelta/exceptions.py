class SASLError(Exception):

    def __init__(self, sasl, text, mech=None):
        """
        :param sasl: The main `suelta.SASL` object.
        :param text: Descpription of the error.
        :param mech: Optional reference to the mechanism object.

        :type sasl: `suelta.SASL`
        """
        self.sasl = sasl
        self.text = text
        self.mech = mech

    def __str__(self):
        if self.mech is None:
            return 'SASL Error: %s' % self.text
        else:
            return 'SASL Error (%s): %s' % (self.mech, self.text)


class SASLCancelled(SASLError):

    def __init__(self, sasl, mech=None):
        """
        :param sasl: The main `suelta.SASL` object.
        :param mech: Optional reference to the mechanism object.

        :type sasl: `suelta.SASL`
        """
        super(SASLCancelled, self).__init__(sasl, "User cancelled", mech)
