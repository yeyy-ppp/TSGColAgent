package humaneval.correct;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;

public class FIND_MAX {
    public static String find_max(String[] words) {
        ArrayList<String> words_list = new ArrayList<String>(Arrays.asList(words));
        Collections.sort(
            words_list,
            (w1, w2) -> {
                Character[] c1 = ((String) w1).chars().mapToObj(c -> (char)c).toArray(Character[]::new);
                HashSet<Character> s1 = new HashSet<Character>(Arrays.asList(c1));
                Character[] c2 = ((String) w2).chars().mapToObj(c -> (char)c).toArray(Character[]::new);
                HashSet<Character> s2 = new HashSet<Character>(Arrays.asList(c2));
                if (s2.size() != s1.size()) return s2.size() - s1.size();
                else return w1.compareTo(w2);
            }
        );
        return words_list.get(0);
    }
}
