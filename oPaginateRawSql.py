import flask_sqlalchemy.extension
import sqlalchemy.engine.base
from sqlalchemy.sql import text, elements, selectable

#----------------------------------------------------------------------------
# This class is fully documented in PaginateRawSql.rst
#----------------------------------------------------------------------------

class PaginateRawSql():

    class PaginateRawSqlError(Exception):
        pass

    def __init__(self,db_con,sqltext,page,per_page, paradict={}):
        '''
        Initialise a paging construct.
        This class is fully documented in PaginateRawSql.rst
        :param db_con: an sqlalchemy connection object.  Typically db.session.connection()
        :param sqltext: EITHER a string containing an sql statement OR a sqlalchemy.sql.text object.  May include column defitinions
        :param page: The page to be displayed
        :param per_page: The number of rows on each page
        :param paradict: If the sql statement contains parameters, then this must be a dictionary contain the values for those parameters.
        '''
        # validate parameters
        if not isinstance(db_con,sqlalchemy.engine.base.Connection):
            raise self.PaginateRawSqlError('The first parameter must be a database connection')
        if not isinstance(sqltext,str) and not isinstance(sqltext,sqlalchemy.sql.elements.TextClause) and not isinstance(sqltext,sqlalchemy.sql.selectable.TextualSelect):
            raise self.PaginateRawSqlError('Parameter two must be either a string containing an sql statement or an sqlalchemy.sql.text object')
        if not isinstance(page,int):
            raise self.PaginateRawSqlError('The page parameter must be an integer')
        if not isinstance(per_page,int):
            raise self.PaginateRawSqlError('The per_page parameter must be an integer')
        if not isinstance(paradict,dict):
            raise self.PaginateRawSqlError('Paradict parameter must be a dictionary containing the values for any sql parameters')
        if page <= 0:
            raise self.PaginateRawSqlError('Page number must not be less than 1')
        # set instance variables
        self.__con = db_con # self.__db.session.connection()
        self.__page = page
        self.__per_page = per_page
        self.__current_item = 0
        if isinstance(sqltext,sqlalchemy.sql.elements.TextClause):
            self.__sqlstring = sqltext.text
        elif isinstance(sqltext, sqlalchemy.sql.selectable.TextualSelect):
            self.__sqlstring = sqltext.element.text
        else:
            self.__sqlstring = sqltext
        self.__paradict = paradict
        self.__sql = self.__add_limit_and_offset(self.__sqlstring)
        self.__totalrows = self.__rowcount(self.__sqlstring,paradict)
        self.__pagecount = int(self.__totalrows / per_page) + 1
        if self.__page > self.__pagecount:
            self.__page = self.__pagecount
        self.__paras = paradict
        self.__paras['perpage'] = self.__per_page
        self.__paras['page'] = (self.__page - 1) * self.__per_page
        thissqltextobj = text(self.__sql)
        if isinstance(sqltext,sqlalchemy.sql.selectable.TextualSelect):
            thissqltextobj = sqlalchemy.sql.selectable.TextualSelect(thissqltextobj, columns=sqltext.columns)
        try:
            self.__rows = self.__con.execute(thissqltextobj,self.__paras).all()
        except KeyError as e:
            raise self.PaginateRawSqlError('Look like you have forgotten some parameters for the query')
        except Exception as e:
            raise self.PaginateRawSqlError(str(e))

    #----------------------------------------------------------------------------
    # Properties required by the pagination object
    # needs first (int), has_next(bool), has_prev(bool), items, last(int) max_per_page(int), next_num(int) page(int) pages(int) per_page(int) prev_num(int), total(int)
    #----------------------------------------------------------------------------

    @property
    def has_next(self):
        if self.__page >= self.__pagecount:
            return False
        else:
            return True

    @property
    def has_prev(self):
        if self.__page == 1:
            return False
        else:
            return True

    @property
    def page(self):
        # this is the current page number
        return self.__page

    @property
    def pages(self):
        # this is the current page number
        return self.__pagecount

    @property
    def first(self):
        #This should be the first ROW number of the CURRENT page
        return (self.page - 1) * self.__per_page + 1

    @property
    def last(self):
        #this is the last ROW Number of the CURRENT page
        if (self.page - 1) * self.__per_page + self.__per_page >= self.__totalrows:
            return self.__totalrows
        return (self.page - 1) * self.__per_page + self.__per_page

    @property
    def per_page(self):
        return self.__per_page

    @property
    def next_num(self):
        if self.__page >= self.__page:
            return self.__pagecount
        else:
            return self.__page + 1

    @property
    def prev_num(self):
        if self.__page > 1:
            return self.__page - 1
        else:
            return 0

    @property
    def next(self):
        if self.__page == self.__pagecount:
            return PaginateRawSql(self.__con, self.__sqlstring, self.__page, self.__per_page, self.__paradict)
        else:
            return PaginateRawSql(self.__con, self.__sqlstring, self.__page + 1, self.__per_page, self.__paradict)

    @property
    def prev(self):
        if self.__page == 1:
            return PaginateRawSql(self.__con, self.__sqlstring, self.__page, self.__per_page, self.__paradict)
        else:
            return PaginateRawSql(self.__con, self.__sqlstring, self.__page - 1, self.__per_page, self.__paradict)

    @property
    def total(self):
        return self.__totalrows

    #----------------------------------------------------------------------------
    # Properties NOT required by the pagination object
    #----------------------------------------------------------------------------

    @property
    def rows(self):
        return self.__rows

    #----------------------------------------------------------------------------
    # Methods required by the pagination object
    #----------------------------------------------------------------------------

    def iter_pages(self, left_edge=2,left_current=2,right_current=5,right_edge=2):
        #Todo: fix this
        # The iter_pages() method is especially interesting.
        # The method actually takes up to 4 arguments: left_edge, left_current, right_current, and right_edge, which are all integers.
        # .
        # The left_edge argument is the number of pages to display starting from 1
        # The 'left_current` argument is the number of pages to display before the current page
        # The 'right_current` argument is the number of pages to display after the current page
        # The right_edge argument is the number of pages to display ending from the last page
        # With default values of 2, 2, 5, and 2, respectively, that means calling the iter_pages() method while
        # on page 10 out of 20 would iterate these pages, in order: 1, 2, None, 8, 9, 10, 11, 12, 13, 14, 15, None, 19, 20. None?!
        # How can you be on page None? A None value actually indicates a gap in the sequence of pages. So you might see "..."
        # to indicate some page numbers aren't displayed. If this all doesn't quite make sense,
        # it will once you give a shot at making a pagination widget yourself.
        # .
        # The Pagination object has attributes that can be used to create a page selection widget by iterating over
        # page numbers and checking the current page. iter_pages() will produce up to three groups of numbers, separated by None.
        # It defaults to showing 2 page numbers at either edge, 2 numbers before the current, the current, and 4 numbers after the current.
        # For example, if there are 20 pages and the current page is 7, the following values are yielded.

        # if there are less than 12 pages just return the whole list
        if self.__pagecount <= 12:
            return list(range(1,self.__pagecount + 1))
        # If we are here then we have more than 12 pages.
        #
        #  We build three lists; the left edge list, the right edge list and the middle page list
        leftedgelist = []
        rightedgelist = []
        # -------middle pagelist-------------------------------------
        # start with the middle pages because we need  the first and last elements when building the edge lists.
        middlepagelist = list(range(self.__page - left_current, self.__page + right_current + 1))  # initialise the list with the middle pages.
        # remove negative items and items greater than the page count
        middlepagelist = [i for i in middlepagelist if i > 0 and i <= self.__pagecount]
        # ---------- left edge ------------------------------
        # Now add the left edge
        leftedgelist = list(range(1,left_edge + 1))
        # remove items from the left edge that are greater than or equal to the first item in pagelist
        leftedgelist = [i for i in leftedgelist if i < middlepagelist[0]]
        # add none if the leftedgelist is full and the last item is less than the first of the page list.
        if len(leftedgelist) >= left_edge and leftedgelist[-1] + 1 < middlepagelist[0] :
            leftedgelist.append(None)
        # ---------- right edge ------------------------------
        rightedgelist = list(range(self.__pagecount + 1 - right_edge,self.__pagecount + 1))
        # remove items from the right edge that are less than the last item in the page list
        rightedgelist = [i for i  in rightedgelist if i > middlepagelist[-1] ]
        # add none if there is a gap between the last item on the pagelist and first item on the right edge list
        if len(rightedgelist) > 0 and  middlepagelist[-1] + 1 < rightedgelist[0]:
            rightedgelist = [None] + rightedgelist


        return leftedgelist + middlepagelist + rightedgelist


    def __iter__(self):
        # returns the iterator object itself
        self.__current_item = 0
        return self

    def __next__(self):
        #return the next item when it is called
        # print(f'current : {self.__current_item}')
        if self.__current_item >= len(self.rows):
            raise StopIteration
        return_row = self.__rows[self.__current_item]
        self.__current_item += 1
        return return_row

    #----------------------------------------------------------------------------
    # Internal and other methods
    #----------------------------------------------------------------------------

    def __add_limit_and_offset(self,thissql):
        # The sql must contain all of "limit" ":perpage", "offset",":page"
        # or none.  We put boolean values in a list to make the checking eaier
        return "select * from (" + thissql +') t0 limit :perpage offset :page'

    def __rowcount(self,thissql,paradict):
        countsql = "select count(*) from (" + thissql + ') t0'
        countrows = self.__con.execute(text(countsql),paradict).first()
        return countrows[0]

