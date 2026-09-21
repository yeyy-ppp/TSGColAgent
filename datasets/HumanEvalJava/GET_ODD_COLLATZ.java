package humaneval.correct;

import java.util.ArrayList;
import java.util.Collections;

public class GET_ODD_COLLATZ {
    public static ArrayList<Integer> get_odd_collatz(int n) {
        ArrayList<Integer> result = new ArrayList<>();
        if((n % 2) == 1) result.add(n);
        while(n > 1) {
            if((n % 2) == 0) n /= 2;
            else n = 3 * n + 1;
            if((n % 2) == 1) result.add(n);
        }
        Collections.sort(result);
        return result;
    }
}
