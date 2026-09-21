package humaneval.correct;

import java.util.ArrayList;
import java.util.Collections;

public class IS_NESTED {
    public static boolean is_nested(String brackets) {
        ArrayList<Integer> opening_brackets = new ArrayList<>();
        ArrayList<Integer> closing_brackets = new ArrayList<>();
        for(int i = 0; i < brackets.length(); i++) {
            if(brackets.charAt(i) == '[') opening_brackets.add(i);
            else closing_brackets.add(i);
        }
        Collections.reverse(closing_brackets);
        int cnt = 0, i = 0, l = closing_brackets.size();
        for(int idx : opening_brackets) {
            if(i < l && idx < closing_brackets.get(i)) {
                i++;
                cnt++;
            }
        }
        return cnt >= 2;
    }
}
