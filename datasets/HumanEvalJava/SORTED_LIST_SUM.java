package humaneval.correct;

import java.util.ArrayList;
import java.util.Collections;

public class SORTED_LIST_SUM {
    public static ArrayList<String> sorted_list_sum(ArrayList<String> lst) {
        ArrayList<String> result = new ArrayList<String>();
        for (String str : lst) {
            if (str.length() % 2 == 1) continue;
            result.add(str);
        }
        Collections.sort(
            result,
            (s1, s2) -> {
                if (s1.length() == s2.length()) return s1.compareTo(s2);
                return s1.length() - s2.length();
            }
        );
        return result;
    }
}
