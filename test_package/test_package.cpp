#include <hunspell/hunspell.hxx>
#include <string>
#include <iostream>

int main()
{
    Hunspell spell("en_US.aff", "en_US.dic");

    std::string word = "apple";
    std::cout << "Testing word: " << word << std::endl;
    if (spell.spell(word.c_str()) == 0)
    {
        std::cout << "Spelling Error!" << std::endl;
    }
    else
    {
        std::cout << "Correct Spelling!" << std::endl;
    }

    word = "abple";
    std::cout << "Testing word: " << word << std::endl;
    if (spell.spell(word.c_str()) == 0)
    {
        std::cout << "Spelling Error!" << std::endl;
    }
    else
    {
        std::cout << "Correct Spelling!" << std::endl;
    }
    return 0;
}
