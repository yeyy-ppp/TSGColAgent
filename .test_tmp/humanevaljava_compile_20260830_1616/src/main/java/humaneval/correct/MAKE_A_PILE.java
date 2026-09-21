package humaneval.correct;

import java.util.ArrayList;

public class MAKE_A_PILE {
	public static ArrayList<Integer> make_a_pile(int n) {
		ArrayList<Integer> pile = new ArrayList<Integer>();
		for(int i = 0; i < n; i++) {
			pile.add(n + 2 * i);
		}
		return pile;
	}
}
