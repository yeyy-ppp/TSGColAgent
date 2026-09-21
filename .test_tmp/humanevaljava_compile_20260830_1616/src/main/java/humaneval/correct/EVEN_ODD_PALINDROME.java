package humaneval.correct;

import java.util.ArrayList;
import java.util.Arrays;

public class EVEN_ODD_PALINDROME {
    public static boolean is_palindrome(int n) {
        String n_str = Integer.toString(n);
        String n_str_rev = "";
        for(int i = n_str.length() - 1; i >= 0; i--) {
            n_str_rev += n_str.substring(i, i + 1);
        }
        return n_str.equals(n_str_rev);
    }
    public static ArrayList<Integer> even_odd_palindrome(int n) {
        int even_palindrome_count = 0, odd_palindrome_count = 0;
        for(int i = 1; i <= n; i++) {
            if((i % 2) == 1 && is_palindrome(i)) odd_palindrome_count++;
            else if((i % 2) == 0 && is_palindrome(i)) even_palindrome_count++;
        }
        ArrayList<Integer> result = new ArrayList<>(Arrays.asList(even_palindrome_count, odd_palindrome_count));
        return result;
    }
}
