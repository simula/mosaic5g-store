import argparse
#http://andreinc.net/2010/10/05/converting-infix-to-rpn-shunting-yard-algorithm/
#http://danishmujeeb.com/blog/2014/12/parsing-reverse-polish-notation-in-python/
#Associativity constants for operators
LEFT_ASSOC = 0
RIGHT_ASSOC = 1
 
#Supported operators
OPERATORS = {
    '+' : (0, LEFT_ASSOC),
    '-' : (0, LEFT_ASSOC),
    '*' : (5, LEFT_ASSOC),
    '/' : (5, LEFT_ASSOC),
    '%' : (5, LEFT_ASSOC),
    '^' : (10, RIGHT_ASSOC)
}
 
#Test if a certain token is operator
def isOperator(token):
    return token in OPERATORS.keys()
 
#Test the associativity type of a certain token
def isAssociative(token, assoc):
    if not isOperator(token):
        raise ValueError('Invalid token: %s' % token)
    return OPERATORS[token][1] == assoc
 
#Compare the precedence of two tokens
def cmpPrecedence(token1, token2):
    if not isOperator(token1) or not isOperator(token2):
        raise ValueError('Invalid tokens: %s %s' % (token1, token2))
    return OPERATORS[token1][0] - OPERATORS[token2][0]
 
#Transforms an infix expression to RPN
def infixToRPN(tokens):
    out = []
    stack = []
    #For all the input tokens [S1] read the next token [S2]
    for token in tokens:
        if isOperator(token):
            # If token is an operator (x) [S3]
            while len(stack) != 0 and isOperator(stack[-1]):
                # [S4]
                if (isAssociative(token, LEFT_ASSOC)
                    and cmpPrecedence(token, stack[-1]) <= 0) or \
                    (isAssociative(token, RIGHT_ASSOC)
                    and cmpPrecedence(token, stack[-1]) < 0):
                    # [S5] [S6]
                    out.append(stack.pop())
                    continue
                break
            # [S7]
            stack.append(token)
        elif token == '(':
            stack.append(token) # [S8]
        elif token == ')':
            # [S9]
            while len(stack) != 0 and stack[-1] != '(':
                out.append(stack.pop()) # [S10]
            stack.pop() # [S11]
        else:
            out.append(token) # [S12]
    while len(stack) != 0:
        # [S13]
        out.append(stack.pop())
    return out

def parse_rpn(expression):
    """ Evaluate a reverse polish notation """
 
    stack = []
 
    for val in expression:
        if val in ['-', '+', '*', '/', '^']:
            op1 = stack.pop()
            op2 = stack.pop()
            if val=='-': result = op2 - op1
            if val=='+': result = op2 + op1
            if val=='*': result = op2 * op1
            if val=='/': result = op2 / op1
            if val=='^': result = op2 ** op1
            stack.append(result)
        else:
            stack.append(float(val))
 
    return stack.pop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some input.')
    
    parser.add_argument('--pattern', metavar='[option]', action='store', type=str,
                        required=True, default='2 2 +', 
                        help='set math pattern')
    args = parser.parse_args();

    print 'pattern: ', args.pattern

    #print 'result: ', parse_rpn(args.pattern)

    input = args.pattern.split(" ")
    output = infixToRPN(input)
    print 'rpn pattern', output

    for i in range(len(output)):
        if output[i] == 'freq':
            output[i] = '3'
            #print 'assign 3 to freq'
    
    try:
        result = parse_rpn(output)
        print parse_rpn(output)
    except:
        print 'Wrong parameters names or pattern'


