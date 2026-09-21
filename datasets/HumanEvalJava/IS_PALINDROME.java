package humaneval.correct;

public class IS_PALINDROME {
    public static boolean is_palindrome(String text) {
        for (int i = 0; i < text.length(); i += 1){
            if (text.charAt(i) != text.charAt(text.length() - i - 1))
                return false;
        }
        return true;
    }
}
