/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package thesis;

import java.io.IOException;
import org.json.simple.parser.ParseException;
import thesis.beans.Sentence;

/**
 *
 * @author ari
 */
public class ReadabilityTest {

    public static void main(String[] args) throws IOException, ParseException {
        //String sentence = "Eric is one of the teachers.";
        //String sentence ="Eric è un professore.";
        String sentence = "Vargo har placerat alla pengar i hennes fond";
        Sentence s = new Sentence(sentence);
        s.setLanguage(Language.English);
        ReadabilityEstimator est = ReadabilityEstimator.getInstance();
        est.calculateReadability(s);
        System.out.println(s.getComplexity());
    }
}
