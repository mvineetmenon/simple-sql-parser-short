from lexer import Lexer


class AST(object):
    def __str__(self):
        return self.__class__.__name__ + ": "


class USEStatement(AST):
    def __init__(self, db_name):
        self.db_name = db_name
        self.token = self.op = 'USE'

    def __str__(self):
        return "{0}{1}".format(super(USEStatement, self).__str__(),
                               {'db_name': self.db_name.__str__()}.__str__())


class SELECTStatement(AST):
    def __init__(self, col_lst, table_name):
        self.col_val = col_lst
        self.table_name = table_name
        self.token = self.op = 'SELECT'
        self.where_clause = None
        self.order_by = None

    def add_where(self, where_clause):
        self.where_clause = where_clause

    def add_order_by(self, order_by):
        self.order_by = order_by

    def __str__(self):
        return "{0}{1}".format(super(SELECTStatement, self).__str__(),
                               {'table_name': self.table_name.__str__(),
                                'col_val': self.col_val.__str__(),
                                'where_clause': self.where_clause.__str__(),
                                'order_by': self.order_by.__str__()}.__str__())

class INSERTStatement(AST):
    def __init__(self, table_name, col_lst, val_lst):
        self.table_name = table_name
        self.col_lst = col_lst
        self.val_lst = val_lst

    def __str__(self):
        return "{0}{1}".format(super(INSERTStatement, self).__str__(),
                               {'table_name': self.table_name.__str__(),
                                'col_lst': self.col_lst.__str__(),
                                'val_lst': self.val_lst.__str__()}.__str__())



class DELETEStatement(AST):
    def __init__(self, table_name, condition = None):
        self.table_name = table_name
        self.condition = condition

    def __str__(self):
        return "{0}{1}".format(super(DELETEStatement, self).__str__(),
                               {'table_name': self.table_name.__str__(),
                                'where_clause': self.condition.__str__()}.__str__())


class ColList(AST):
    def __init__(self, col):
        self.col = [col]

    def add_col(self, col):
        self.col.append(col)

    def __str__(self):
        return "{0}{1}".format(super(ColList, self).__str__(), ', '.join(c.__str__() for c in self.col))


class ValList(AST):
    def __init__(self, val):
        self.val = [val]

    def add_val(self, val):
        self.val.append(val)

    def __str__(self):
        return "{0}{1}".format(super(ValList, self).__str__(), ', '.join(c.__str__() for c in self.val))



class Identifier(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.val

    def __str__(self):
        return self.value


class Literal(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.val

    def __str__(self):
        return self.value



class ComparisionOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

    def __str__(self):
        return super(ComparisionOp, self).__str__() + \
               {'operator':self.token.val.__str__(),
                'left_operand': self.left.__str__(),
                'right_operand': self.right.__str__()}.__str__()



class NegOp(AST):
    def __init__(self, op, right):
        self.token = self.op = op
        self.right = right

    def __str__(self):
        return super(NegOp, self).__str__() + {'operand':self.right.__str__()}.__str__()



class NULL(AST):
    def __init__(self):
        pass

    def __str__(self):
        return 'NULL'


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.next()

    def error(self):
        raise Exception('Invalid syntax')

    def next(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then assign the next token to
        # the self.current_token, otherwise raise an exception.
        if not self.current_token:
            self.error()
        if self.current_token.type == token_type:
            self.current_token = self.lexer.next()
        else:
            self.error()

    def identifier(self):
        token = self.current_token
        if token.type == 'IDENTIFIER':
            self.next('IDENTIFIER')
            return Identifier(token)
        else:
            self.error()

    def col_list(self):
        """ col_list := IDENTIFIER | IDENTIFIER SEPARATOR col_list"""
        node_id = self.identifier()
        node = ColList(node_id)

        while self.current_token.type == 'SEPARATOR':
            self.next('SEPARATOR')
            node_id = self.identifier()
            node.add_col(node_id)
        return node

    def select(self):
        """ select := SELECT col_list FROM IDENTIFIER WHERE conditions ORDER BY IDENTIFIER;"""
        col_list = self.col_list()
        self.next('FROM')
        table_name = self.identifier()
        node = SELECTStatement(col_list, table_name)
        if self.current_token.type == 'WHERE':
            self.next('WHERE')
            where_clause = self.condition()
            node.add_where(where_clause)
        if self.current_token.type == 'ORDER':
            self.next('ORDER')
            if self.current_token.type == 'BY':
                self.next('BY')
                order_by_identifier = self.identifier()
                node.add_order_by(order_by_identifier)
            else:
                self.error()
        self.next('EOL')
        return node

    def insert(self):
        """ insert := INSERT INTO IDENTIFIER LP col_list RP VALUES LP val_list RP;"""
        if self.current_token.type == 'INTO':
            self.next('INTO')
            table_name = self.identifier()
            self.next('LP')
            col_list = self.col_list()
            self.next('RP')
            self.next('VALUES')
            self.next('LP')
            val_list = self.val_list()
            self.next('RP')
            self.next('EOL')
            return INSERTStatement(table_name, col_list, val_list)
        else:
            self.error()

    def delete(self):
        """ delete := DELETE FROM IDENTIFIER WHERE condition;"""
        self.next('FROM')
        table_name = self.identifier()
        if self.current_token.type == 'WHERE':
            self.next('WHERE')
            condition = self.condition()
        else:
            condition = None
        self.next('EOL')
        return DELETEStatement(table_name, condition)

    def use(self):
        """ use := USE IDENTIFIER;"""
        db_name = self.identifier()
        self.next('EOL')
        return USEStatement(db_name)


    def val(self):
        """ val := STRING_LITERAL | NUMBER | SQL_FUNCTION """
        token = self.current_token
        if token.type == 'STRING_LITERAL' or token.type == 'NUMBER' or token.type == 'SQL_FUNCTION':
            self.next(token.type)
            return Literal(token)
        else:
            self.error()

    def val_list(self):
        """ val_list := val | val SEPARATOR val_list"""
        node_id = self.val()
        node = ValList(node_id)

        while self.current_token.type == 'SEPARATOR':
            self.next('SEPARATOR')
            node_id = self.val()
            node.add_val(node_id)
        return node

    def null(self):
        """ null := NULL """
        if self.current_token.type == 'NULL':
            self.next('NULL')
            return NULL()
        else:
            self.error()

    def condition(self):
        """ condition := identifier EQ_OP val
            condition := identifier IS NULL
            condition := identifier IS NOT NULL
        """
        left = self.identifier()
        op = self.current_token
        if op.type == 'IS_OP':
            self.next('IS_OP')
            if self.current_token.type == 'NEG_OP':
                self.next('NEG_OP')
                neg_node = NegOp(self.current_token, self.null())
                node = ComparisionOp(left, op, neg_node)
            else:
                node = ComparisionOp(left, op, self.null())
        elif op.type == 'EQ_OP':
            self.next('EQ_OP')
            node = ComparisionOp(left, op, self.val())
        else:
            node = None
            self.error()
        return node

    def parse(self):
        token = self.current_token
        if token.type == 'SELECT':
            self.next('SELECT')
            return self.select()
        elif token.type == 'INSERT':
            self.next('INSERT')
            return self.insert()
        elif token.type == 'DELETE':
            self.next('DELETE')
            return self.delete()
        elif token.type == 'USE':
            self.next('USE')
            return self.use()


if __name__ == "__main__":

    for f in open("operations.sql"):
        print(Parser(Lexer(f)).parse())
