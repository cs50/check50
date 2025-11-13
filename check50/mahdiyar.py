def convert(text):
    text = text.replace("(:" , "😃")
    text = text.replace("):" , "😞")
    return text
def main():
    user_input = input("what's emoji?")
    convert_text = convert(user_input)
    print(convert_text)
if __name__ =="__main__":
    main()
